"""Stage-D batch ``carrier_channels`` -- per-unit L0+L1+L2 coverage of
``error_coupling_simulator.carrier.channels`` (32 CPU-pure public units; pure numpy + scipy,
no torch, no quimb, so out_of_scope is empty).

Full-coverage program (docs/twin_validation/wave2_6_unit_test_contract.md SS12.3/12.4;
work-list docs/twin_validation/l3_release_package_unit_inventory.md D13). ``carrier/channels.py``
is the QUANTUM-CHANNEL LIBRARY of the carrier: rotation unitaries, one/two-qubit + qutrit Kraus
channels, the Wood-Gambetta leakage superoperator/Kraus (scipy.linalg.expm of a Lindbladian),
the readout-bias matrix, and the MechanismSpec contract/dispatch layer over M0..M34.

THE CENTRAL RULE (the standing lesson: assert_cptp/assert_unitary are NECESSARY but VACUOUS as
the ONLY check -- a WRONG channel is usually still CPTP, a wrong rotation still unitary). So EVERY
channel/unitary carries an INDEPENDENT closed-form VALUE-PIN of the actual returned operator
against the textbook form recomputed FROM SCRATCH here (rotations vs scipy.linalg.expm(-i th/2 P)
computed independently of the module's cos/sin body; Kraus vs the textbook Kraus set; the WG
leakage channel vs an INDEPENDENT expm of a from-scratch Lindbladian generator, pinned at the
channel/superoperator level since the operator-sum form is basis-free), plus an
``assert_discriminates`` whose WRONG variant is still structurally CPTP/unitary but fails the pin.

assert_pins casts to float64 (it is float-only), so complex operators are pinned via ``_pin`` --
a thin wrapper that feeds the real+imag components to assert_pins (the mandated discrimination
core, imaginary-part aware). Every RAISE asserts its EXACT message; every contract/audit dict is
pinned with its EXACT string literals + structure (mutmut mutates string constants); every
mechanism_channel branch is exercised at its DEFAULT params so a mutated default constant diverges.
"""
from __future__ import annotations

import math

import numpy as np
import pytest
import scipy.linalg as sla

from _support.faithfulness import (
    assert_cptp,
    assert_discriminates,
    assert_pins,
    assert_row_stochastic,
    assert_unitary,
)

import error_coupling_simulator.carrier.channels as ch
from error_coupling_simulator.carrier.channels import (
    MechanismSpec,
    amplitude_damping_kraus,
    canonical_single_qubit_axis,
    controlled_phase_error_unitary,
    correlated_relaxation_kraus,
    custom_non_pauli_kraus,
    drifted_axis_mixture_kraus,
    leakage_channel_super,
    leakage_kraus,
    leakage_relaxation_surrogate_kraus,
    mechanism_channel,
    mechanism_definition_contract,
    mechanism_error_axis,
    mechanism_operation_axis,
    pauli_stochastic_kraus,
    phase_damping_canonical_kraus,
    phase_damping_kraus,
    readout_bias_matrix,
    reset_to_state_kraus,
    rx_unitary,
    rxx_ryy_unitary,
    rxx_unitary,
    ry_unitary,
    ryy_unitary,
    rz_unitary,
    rzz_unitary,
    single_axis_rotation,
    thermal_excitation_kraus,
    thermal_relaxation_kraus,
    two_pauli_rotation,
    two_qubit_depolarizing_kraus,
    weak_type4_mixing_kraus,
)

_NZ = 1e-12  # NUMERICAL_ZERO (project constant -- independent copy, not the module's symbol)


# --------------------------------------------------------------------------- #
# INDEPENDENT primitives (from scratch -- NOT the module's private helpers)   #
# --------------------------------------------------------------------------- #
_I = np.eye(2, dtype=np.complex128)
_X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
_Y = np.array([[0.0, -1j], [1j, 0.0]], dtype=np.complex128)
_Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
_P = {"I": _I, "X": _X, "Y": _Y, "Z": _Z}


def _pin(actual, reference, *, atol: float = 1e-11, rtol: float = 0.0, label: str = "op",
         check_dtype: bool = True) -> None:
    """Complex-aware value-pin delegating to the mandated float-only ``assert_pins`` on the
    interleaved real+imag components (so imaginary-part mutations are caught). Also asserts the
    module's declared house dtype complex128 (a real behavioral contract downstream code relies
    on -- a `dtype=np.complex128`->`dtype=None` mutation drops a real-valued operator to float64,
    which this catches while an all-complex operator legitimately still infers complex128)."""
    a_raw = np.asarray(actual)
    if check_dtype and isinstance(actual, np.ndarray):
        assert a_raw.dtype == np.complex128, f"{label}: dtype {a_raw.dtype} != complex128"
    a = a_raw.astype(np.complex128)
    r = np.asarray(reference, dtype=np.complex128)
    assert a.shape == r.shape, f"{label}: shape {a.shape} != {r.shape}"
    assert_pins(np.concatenate([a.real.ravel(), a.imag.ravel()]),
                np.concatenate([r.real.ravel(), r.imag.ravel()]),
                atol=atol, rtol=rtol, label=label)


def _pin_set(actual_list, reference_list, *, atol: float = 1e-11, label: str = "kraus",
             check_dtype: bool = True) -> None:
    """Pin a Kraus/operator LIST elementwise (count + every entry + house dtype)."""
    a = list(actual_list)
    r = list(reference_list)
    assert len(a) == len(r), f"{label}: count {len(a)} != {len(r)}"
    for i, (ai, ri) in enumerate(zip(a, r)):
        _pin(np.asarray(ai), ri, atol=atol, label=f"{label}[{i}]", check_dtype=check_dtype)


def _floor(v: float) -> float:
    """probability_floor recomputed from scratch: min(1, max(1e-12, v))."""
    return min(1.0, max(_NZ, float(v)))


def _pos_floor(v: float) -> float:
    return max(_NZ, float(v))


# -- rotations via an INDEPENDENT matrix exponential (exact for these small generators) -- #
def _expm_rot(theta: float, gen: np.ndarray) -> np.ndarray:
    """exp(-i theta/2 * gen), computed by scipy.linalg.expm -- independent of the cos/sin body."""
    return sla.expm(-0.5j * float(theta) * np.asarray(gen, dtype=np.complex128))


def _rx(t):  return _expm_rot(t, _X)
def _ry(t):  return _expm_rot(t, _Y)
def _rz(t):  return _expm_rot(t, _Z)
def _rzz(t): return _expm_rot(t, np.kron(_Z, _Z))
def _rxx(t): return _expm_rot(t, np.kron(_X, _X))
def _ryy(t): return _expm_rot(t, np.kron(_Y, _Y))


def _axis_u(axis: str, theta: float) -> np.ndarray:
    return {"rx": _rx, "ry": _ry, "rz": _rz}[axis](theta)


def _cphase(theta: float) -> np.ndarray:
    return np.diag([1.0, 1.0, 1.0, np.exp(-1j * float(theta))]).astype(np.complex128)


def _two_pauli(theta: float, left: str, right: str) -> np.ndarray:
    return _expm_rot(theta, np.kron(_P[left], _P[right]))


def _single_axis(theta: float, comps) -> np.ndarray:
    op = np.zeros((2, 2), dtype=np.complex128)
    nsq = 0.0
    for lab, val in comps.items():
        c = float(val)
        op = op + c * _P[str(lab).upper()]
        nsq += c * c
    gen = op / math.sqrt(max(nsq, _NZ))
    return math.cos(0.5 * theta) * _I - 1j * math.sin(0.5 * theta) * gen


# -- Kraus channels, textbook forms recomputed from scratch -- #
def _amp(g):
    g = _floor(g)
    return [np.array([[1.0, 0.0], [0.0, math.sqrt(1.0 - g)]], np.complex128),
            np.array([[0.0, math.sqrt(g)], [0.0, 0.0]], np.complex128)]


def _phase_z(g):
    g = _floor(g)
    return [math.sqrt(_pos_floor(1.0 - g)) * _I, math.sqrt(g) * _Z]


def _phase_canon(l):
    l = _floor(l)
    return [np.array([[1.0, 0.0], [0.0, math.sqrt(_pos_floor(1.0 - l))]], np.complex128),
            np.array([[0.0, 0.0], [0.0, math.sqrt(l)]], np.complex128)]


def _thermal(t, t1, t2):
    gamma = 1.0 - math.exp(-t / t1)
    inv = 1.0 / t2 - 1.0 / (2.0 * t1)
    lam = 1.0 - math.exp(-2.0 * t * inv) if inv > 0.0 else 0.0
    ad, pd = _amp(gamma), _phase_canon(lam)
    return [p @ a for a in ad for p in pd]


def _thermal_exc(g):
    g = _floor(g)
    return [np.array([[math.sqrt(1.0 - g), 0.0], [0.0, 1.0]], np.complex128),
            np.array([[0.0, 0.0], [math.sqrt(g), 0.0]], np.complex128)]


def _reset(p, target):
    p = _floor(p)
    k0 = math.sqrt(_pos_floor(1.0 - p)) * _I
    k1 = np.zeros((2, 2), np.complex128)
    k2 = np.zeros((2, 2), np.complex128)
    k1[target, 0] = math.sqrt(p)
    k2[target, 1] = math.sqrt(p)
    return [k0, k1, k2]


def _leak_surrogate(p):
    return [d @ ph for d in _amp(p) for ph in _phase_z(p)]


def _corr_relax(g):
    g = _floor(g)
    k0 = np.diag([1.0, 1.0, 1.0, math.sqrt(1.0 - g)]).astype(np.complex128)
    k1 = np.zeros((4, 4), np.complex128)
    k1[0, 3] = math.sqrt(g)
    return [k0, k1]


def _two_qubit_depol(p):
    p = _floor(p)
    labels = [(a, b) for a in "IXYZ" for b in "IXYZ"]
    nonid = [(a, b) for a, b in labels if not (a == "I" and b == "I")]
    each = p / len(nonid)
    out = [math.sqrt(_pos_floor(1.0 - p)) * np.eye(4, dtype=np.complex128)]
    for a, b in nonid:
        out.append(math.sqrt(each) * np.kron(_P[a], _P[b]))
    return out


def _custom_non_pauli(eta):
    e = _floor(eta)
    rot = _rz(0.37) @ _rx(0.23)
    return [item @ rot for item in _amp(e)]


def _weak_type4(eta):
    e = _floor(eta)
    rot = _rz(0.17) @ _rx(0.11)
    return [math.sqrt(_pos_floor(1.0 - 2.0 * e)) * rot,
            math.sqrt(e) * _X @ rot,
            math.sqrt(e) * _Z @ rot]


def _pauli_stoch(probs):
    probs = {str(k).upper(): float(v) for k, v in probs.items()}
    err = sum(_floor(probs.get(k, _NZ)) for k in ("X", "Y", "Z"))
    out = [math.sqrt(_pos_floor(1.0 - err)) * _I]
    for k in ("X", "Y", "Z"):
        out.append(math.sqrt(_floor(probs.get(k, _NZ))) * _P[k])
    return out


def _readout(p0_to_1, p1_to_0):
    p01, p10 = _floor(p0_to_1), _floor(p1_to_0)
    return np.array([[1.0 - p01, p01], [p10, 1.0 - p10]], dtype=np.float64)


# -- WG leakage generator recomputed from scratch (qutrit; column-stacking Lindbladian) -- #
def _qop(a, b):
    ket = np.zeros(3, np.complex128); ket[a] = 1.0
    bra = np.zeros(3, np.complex128); bra[b] = 1.0
    return np.outer(ket, bra.conj())


def _lindblad(H, jumps):
    d = H.shape[0]
    eye = np.eye(d, dtype=np.complex128)
    L = -1j * (np.kron(eye, H) - np.kron(H.T, eye))
    for J in jumps:
        jdj = J.conj().T @ J
        L += np.kron(J.conj(), J) - 0.5 * (np.kron(eye, jdj) + np.kron(jdj.T, eye))
    return L


def _leak_super_ref(theta, g_seep, g_heat, t=1.0):
    H = float(theta) * (_qop(1, 2) + _qop(2, 1))
    jumps = []
    if g_seep > 0.0:
        jumps.append(math.sqrt(g_seep) * _qop(1, 2))
    if g_heat > 0.0:
        jumps.append(math.sqrt(g_heat) * _qop(2, 1))
    return sla.expm(_lindblad(H, jumps) * float(t))


def _super_from_kraus(kraus):
    """Column-stacking channel superoperator S = sum_k conj(K_k) kron K_k -- basis-free identity
    for E(rho)=sum K rho K^dag, matching the module's Fortran-order vec convention."""
    return sum(np.kron(K.conj(), K) for K in kraus)


# =========================================================================== #
# rotation unitaries: rx / ry / rz / rzz                                       #
# =========================================================================== #
def test_L0_rx_ry_rz_pinned_vs_expm_and_unitary():
    for t in (0.0, 0.031, -0.4, 1.3):
        for u, ref, name in ((rx_unitary(t), _rx(t), "rx"), (ry_unitary(t), _ry(t), "ry"),
                             (rz_unitary(t), _rz(t), "rz")):
            assert_unitary(u, label=name)
            _pin(u, ref, atol=1e-12, label=name)
    # explicit closed-form entries (kill a cos/sin swap or a dropped -i on rx)
    c, s = math.cos(0.2), math.sin(0.2)
    _pin(rx_unitary(0.4), np.array([[c, -1j * s], [-1j * s, c]]), atol=1e-12, label="rx entries")
    _pin(ry_unitary(0.4), np.array([[c, -s], [s, c]]), atol=1e-12, label="ry entries")
    _pin(rz_unitary(0.4), np.diag([np.exp(-1j * 0.2), np.exp(1j * 0.2)]), atol=1e-12, label="rz entries")


def test_L0_rzz_pinned_vs_expm_and_diag_structure():
    for t in (0.0, 0.04, -0.7):
        assert_unitary(rzz_unitary(t), label="rzz")
        _pin(rzz_unitary(t), _rzz(t), atol=1e-12, label="rzz")
    # exact diagonal (kills a phase-sign or ordering mutation of the four diag entries)
    pm, pp = np.exp(-0.02j), np.exp(0.02j)
    _pin(rzz_unitary(0.04), np.diag([pm, pp, pp, pm]), atol=1e-12, label="rzz diag")


def test_KILLER_rotations_discriminate():
    t = 0.37
    assert_discriminates(lambda u: _pin(u, _rx(t), atol=1e-12), rx_unitary(t), rx_unitary(-t), label="rx")
    assert_discriminates(lambda u: _pin(u, _ry(t), atol=1e-12), ry_unitary(t), ry_unitary(-t), label="ry")
    assert_discriminates(lambda u: _pin(u, _rz(t), atol=1e-12), rz_unitary(t), rz_unitary(-t), label="rz")
    assert_discriminates(lambda u: _pin(u, _rzz(t), atol=1e-12), rzz_unitary(t), rzz_unitary(-t), label="rzz")


# =========================================================================== #
# two_pauli_rotation + rxx / ryy / rxx_ryy / controlled_phase_error            #
# =========================================================================== #
def test_L0_two_pauli_rotation_pinned_vs_expm_all_labels():
    for left in "IXYZ":
        for right in "IXYZ":
            for t in (0.0, 0.017, -0.3):
                u = two_pauli_rotation(t, left, right)
                assert_unitary(u, label=f"tp[{left}{right}]")
                _pin(u, _two_pauli(t, left, right), atol=1e-12, label=f"tp[{left}{right}]")
    # lower-case labels are upper()-cased inside (kill a dropped .upper())
    _pin(two_pauli_rotation(0.2, "x", "y"), _two_pauli(0.2, "X", "Y"), atol=1e-12, label="tp lower")


def test_L0_rxx_ryy_and_composite_pinned():
    for t in (0.022, -0.5):
        assert_unitary(rxx_unitary(t), label="rxx")
        _pin(rxx_unitary(t), _rxx(t), atol=1e-12, label="rxx")
        assert_unitary(ryy_unitary(t), label="ryy")
        _pin(ryy_unitary(t), _ryy(t), atol=1e-12, label="ryy")
    # composite: ryy(theta_y) @ rxx(theta_x). XX and YY COMMUTE (XY(x)XY = -Z(x)Z = YX(x)YX),
    # so the product is order-independent -- an order swap in the src is a genuine equivalent; the
    # discriminating teeth are on the two DISTINCT angles theta_x != theta_y (not on order).
    tx, ty = 0.025, 0.0175
    comp = rxx_ryy_unitary(theta_x=tx, theta_y=ty)
    assert_unitary(comp, label="rxx_ryy")
    _pin(comp, _ryy(ty) @ _rxx(tx), atol=1e-11, label="rxx_ryy")
    # theta_x and theta_y feed DIFFERENT generators -> swapping the two args changes the unitary
    assert np.max(np.abs(comp - rxx_ryy_unitary(theta_x=ty, theta_y=tx))) > 1e-4


def test_L0_controlled_phase_error_pinned():
    for t in (0.0, 0.035, -0.9):
        u = controlled_phase_error_unitary(t)
        assert_unitary(u, label="cphase")
        _pin(u, _cphase(t), atol=1e-12, label="cphase")
    # only the |11><11| entry carries the phase (kills a mutated diagonal index/sign)
    assert controlled_phase_error_unitary(0.5)[3, 3] == pytest.approx(np.exp(-0.5j))
    assert controlled_phase_error_unitary(0.5)[0, 0] == pytest.approx(1.0)


def test_KILLER_two_pauli_and_cphase_discriminate():
    assert_discriminates(lambda u: _pin(u, _two_pauli(0.3, "X", "Z"), atol=1e-12),
                         two_pauli_rotation(0.3, "X", "Z"), two_pauli_rotation(0.3, "Z", "X"),
                         label="two_pauli order")
    assert_discriminates(lambda u: _pin(u, _cphase(0.4), atol=1e-12),
                         controlled_phase_error_unitary(0.4), controlled_phase_error_unitary(-0.4),
                         label="cphase")


# =========================================================================== #
# single_axis_rotation                                                        #
# =========================================================================== #
def test_L0_single_axis_rotation_pinned_and_unitary():
    for comps in ({"X": 1.0, "Z": 1.0}, {"X": 1.0}, {"Y": 2.0, "Z": 1.0}):
        for t in (0.0, 0.026, -0.4):
            u = single_axis_rotation(t, comps)
            assert_unitary(u, label="single_axis")
            _pin(u, _single_axis(t, comps), atol=1e-12, label="single_axis")
    # a single X-component reduces to rx (generator = X); pins the normalization + generator build
    _pin(single_axis_rotation(0.5, {"X": 1.0}), _rx(0.5), atol=1e-12, label="single_axis==rx")


def test_KILLER_single_axis_rotation_discriminates():
    # a WRONG generator (X+Z with a sign flip: X-Z) is still unitary but a different rotation
    def wrong():
        gen = (_X - _Z) / math.sqrt(2.0)
        return math.cos(0.5 * 0.4) * _I - 1j * math.sin(0.5 * 0.4) * gen
    assert_discriminates(lambda u: _pin(u, _single_axis(0.4, {"X": 1.0, "Z": 1.0}), atol=1e-12),
                         single_axis_rotation(0.4, {"X": 1.0, "Z": 1.0}), wrong(),
                         label="single_axis generator")


# =========================================================================== #
# amplitude / phase / thermal / excitation / reset / leakage-surrogate Kraus   #
# =========================================================================== #
def test_L0_amplitude_damping_pinned_cptp_and_floor():
    for g in (0.0, 0.25, 0.9, 1.0):
        k = amplitude_damping_kraus(g)
        assert_cptp(k, label="amp")
        _pin_set(k, _amp(g), atol=1e-12, label="amp")
    # exact textbook entries at a clean gamma (kills a mutated K0/K1 entry)
    _pin_set(amplitude_damping_kraus(0.25),
             [np.array([[1.0, 0.0], [0.0, math.sqrt(0.75)]]),
              np.array([[0.0, 0.5], [0.0, 0.0]])], atol=1e-12, label="amp entries")
    # gamma=0 is FLOORED to 1e-12 (not exact 0) -> K1 has a sqrt(1e-12) entry, K0 corner < 1
    assert amplitude_damping_kraus(0.0)[1][0, 1] == pytest.approx(math.sqrt(_NZ), abs=1e-18)


def test_L0_phase_damping_variants_pinned_cptp():
    for g in (0.0, 0.2, 0.6, 1.0):
        kz = phase_damping_kraus(g)
        assert_cptp(kz, label="phase_z")
        _pin_set(kz, _phase_z(g), atol=1e-12, label="phase_z")
        kc = phase_damping_canonical_kraus(g)
        assert_cptp(kc, label="phase_canon")
        _pin_set(kc, _phase_canon(g), atol=1e-12, label="phase_canon")
    # the two parameterizations DIFFER (Z-flip prob vs canonical rate) -> not the same channel
    assert np.max(np.abs(np.asarray(phase_damping_kraus(0.3)[1])
                         - np.asarray(phase_damping_canonical_kraus(0.3)[1]))) > 0.1


def test_L0_thermal_relaxation_pinned_map_and_guards():
    # inv_tphi > 0 branch (T2 < 2 T1): exact map rho01 -> exp(-t/T2) rho01
    k = thermal_relaxation_kraus(30.0, 200.0, 150.0)
    assert_cptp(k, label="thermal")
    _pin_set(k, _thermal(30.0, 200.0, 150.0), atol=1e-11, label="thermal")
    # exact off-diagonal contraction: sum_k K rho K^dag has rho01 scaled by exp(-t/T2)
    rho = np.array([[0.3, 0.5 + 0.2j], [0.5 - 0.2j, 0.7]], np.complex128)
    out = sum(K @ rho @ K.conj().T for K in k)
    assert out[0, 1] == pytest.approx(rho[0, 1] * math.exp(-30.0 / 150.0), abs=1e-9)
    # inv_tphi == 0 branch (T2 == 2 T1 exactly -> lam_phi = 0, pure amplitude damping)
    keq = thermal_relaxation_kraus(30.0, 100.0, 200.0)
    _pin_set(keq, _thermal(30.0, 100.0, 200.0), atol=1e-11, label="thermal T2=2T1")
    # guards (exact messages)
    with pytest.raises(ValueError) as e1:
        thermal_relaxation_kraus(1.0, 0.0, 1.0)
    assert str(e1.value) == "T1, T2 must be positive (T1=0.0, T2=1.0)"
    with pytest.raises(ValueError) as e2:
        thermal_relaxation_kraus(1.0, 100.0, 250.0)
    assert str(e2.value) == "unphysical T2 > 2 T1 (T2=250.0, T1=100.0)"


def test_L0_thermal_excitation_and_reset_and_leak_surrogate_pinned():
    for g in (0.0, 0.006, 0.5):
        k = thermal_excitation_kraus(g)
        assert_cptp(k, label="thermal_exc")
        _pin_set(k, _thermal_exc(g), atol=1e-12, label="thermal_exc")
    for target in (0, 1):
        for p in (0.0, 0.018, 0.7):
            k = reset_to_state_kraus(p, target_state=target)
            assert_cptp(k, label="reset")
            _pin_set(k, _reset(p, target), atol=1e-12, label=f"reset t={target}")
    with pytest.raises(ValueError) as er:
        reset_to_state_kraus(0.1, target_state=2)
    assert str(er.value) == "target_state must be 0 or 1"
    for p in (0.004, 0.3):
        k = leakage_relaxation_surrogate_kraus(p)
        assert_cptp(k, label="leak_surrogate")
        _pin_set(k, _leak_surrogate(p), atol=1e-11, label="leak_surrogate")


def test_KILLER_kraus_channels_discriminate():
    assert_discriminates(lambda k: _pin_set(k, _amp(0.25), atol=1e-12),
                         amplitude_damping_kraus(0.25), amplitude_damping_kraus(0.4), label="amp")
    # reset target 0 vs target 1 are both CPTP but different channels
    assert_discriminates(lambda k: _pin_set(k, _reset(0.3, 1), atol=1e-12),
                         reset_to_state_kraus(0.3, target_state=1),
                         reset_to_state_kraus(0.3, target_state=0), label="reset target")


# =========================================================================== #
# correlated_relaxation / two_qubit_depolarizing / custom_non_pauli / weak4    #
# =========================================================================== #
def test_L0_correlated_relaxation_pinned_cptp():
    for g in (0.0, 0.01, 0.5):
        k = correlated_relaxation_kraus(g)
        assert_cptp(k, label="corr_relax")
        _pin_set(k, _corr_relax(g), atol=1e-12, label="corr_relax")
    # only the |11> population relaxes: K1 connects |11> -> |00> exclusively (index-pinned)
    k1 = np.asarray(correlated_relaxation_kraus(0.4)[1])
    assert k1[0, 3] == pytest.approx(math.sqrt(0.4)) and np.count_nonzero(k1) == 1


def test_L0_two_qubit_depolarizing_pinned_cptp_and_weights():
    for p in (0.0, 0.006, 0.6):
        k = two_qubit_depolarizing_kraus(p)
        assert_cptp(k, label="2q_depol")
        _pin_set(k, _two_qubit_depol(p), atol=1e-12, label="2q_depol")
    k = two_qubit_depolarizing_kraus(0.15)
    assert len(k) == 16  # I + 15 non-identity two-qubit Paulis
    # each non-identity weight is p/15 (kills a mutated denominator)
    assert np.asarray(k[1])[0, 1] == pytest.approx(math.sqrt(0.15 / 15.0))


def test_L0_custom_non_pauli_and_weak_type4_pinned_cptp():
    for e in (0.0, 0.02, 0.2):
        k = custom_non_pauli_kraus(e)
        assert_cptp(k, label="custom")
        _pin_set(k, _custom_non_pauli(e), atol=1e-11, label="custom")
    for e in (0.006, 0.1):
        k = weak_type4_mixing_kraus(e)
        assert_cptp(k, label="weak4")
        _pin_set(k, _weak_type4(e), atol=1e-11, label="weak4")


def test_KILLER_two_qubit_depol_discriminates():
    assert_discriminates(lambda k: _pin_set(k, _two_qubit_depol(0.15), atol=1e-12),
                         two_qubit_depolarizing_kraus(0.15), two_qubit_depolarizing_kraus(0.3),
                         label="2q_depol")


# =========================================================================== #
# pauli_stochastic_kraus                                                       #
# =========================================================================== #
def test_L0_pauli_stochastic_pinned_cptp_and_sum_guard():
    for probs in ({"X": 0.01, "Y": 0.02, "Z": 0.03}, {"Z": 0.005}, {}):
        k = pauli_stochastic_kraus(probs)
        assert_cptp(k, label="pauli_stoch")
        _pin_set(k, _pauli_stoch(probs), atol=1e-12, label="pauli_stoch")
    # lower-case keys are upper()-cased (kill a dropped .upper())
    _pin_set(pauli_stochastic_kraus({"x": 0.02}), _pauli_stoch({"X": 0.02}), atol=1e-12, label="pauli lower")
    # sum > 1 raises with the EXACT message
    with pytest.raises(ValueError) as e:
        pauli_stochastic_kraus({"X": 0.5, "Y": 0.5, "Z": 0.5})
    assert str(e.value) == "stochastic Pauli probabilities sum to more than one"
    # sum == 1.0 EXACTLY must NOT raise (kills `> 1.0 + 1e-12` -> `> 1.0 - 1e-12`, which would):
    # error_probability = 1.0 is not > 1.0 + 1e-12, so the identity coefficient floors to sqrt(1e-12).
    k1 = pauli_stochastic_kraus({"X": 0.4, "Y": 0.4, "Z": 0.2})
    assert_cptp(k1, label="pauli sum1")
    _pin_set(k1, _pauli_stoch({"X": 0.4, "Y": 0.4, "Z": 0.2}), atol=1e-12, label="pauli sum1")


def test_L0_pauli_stochastic_floor_keeps_all_three_paulis():
    # DEAD-BRANCH probe (registry exemption): `if p >= NUMERICAL_ZERO` is ALWAYS true because
    # probability_floor(0)=1e-12=NUMERICAL_ZERO, so even a ZERO input Pauli prob yields its
    # sqrt(1e-12) Kraus (the append FIRES). This pins exactly what the `>=`->`>` mutant would drop.
    k = pauli_stochastic_kraus({"X": 0.02})   # Y and Z absent -> floored to 1e-12
    assert len(k) == 4                         # I + X + Y + Z (none dropped)
    _pin(k[2], math.sqrt(_NZ) * _Y, atol=1e-18, label="Y at floor")
    _pin(k[3], math.sqrt(_NZ) * _Z, atol=1e-18, label="Z at floor")


def test_KILLER_pauli_stochastic_discriminates():
    # a permuted-probability variant is still CPTP but a different channel
    assert_discriminates(lambda k: _pin_set(k, _pauli_stoch({"X": 0.01, "Y": 0.02, "Z": 0.03}), atol=1e-12),
                         pauli_stochastic_kraus({"X": 0.01, "Y": 0.02, "Z": 0.03}),
                         pauli_stochastic_kraus({"X": 0.03, "Y": 0.02, "Z": 0.01}), label="pauli_stoch")


# =========================================================================== #
# drifted_axis_mixture_kraus                                                   #
# =========================================================================== #
def _drift_ref(axis, epsilon, span, weights):
    span = abs(span)
    if span <= 0.0:
        return [_axis_u(axis, epsilon)]
    w = [max(0.0, float(x)) for x in weights]
    tot = sum(w)
    norm = [x / tot for x in w]
    offs = (-span, 0.0, span)
    return [math.sqrt(nw) * _axis_u(axis, epsilon + o) for nw, o in zip(norm, offs)]


def test_L0_drifted_axis_mixture_all_branches_pinned():
    # span <= 0 -> single unitary
    z = drifted_axis_mixture_kraus("rx", epsilon=0.03, effective_span=0.0)
    assert len(z) == 1
    _pin(z[0], _rx(0.03), atol=1e-12, label="drift span0")
    # span > 0, weights=None -> default [0.25,0.5,0.25]
    d = drifted_axis_mixture_kraus("ry", epsilon=0.03, effective_span=0.09, weights=None)
    assert_cptp(d, label="drift default")
    _pin_set(d, _drift_ref("ry", 0.03, 0.09, [0.25, 0.5, 0.25]), atol=1e-12, label="drift default")
    # span > 0, valid explicit weights
    dv = drifted_axis_mixture_kraus("rz", epsilon=0.02, effective_span=0.08, weights=[0.2, 0.5, 0.3])
    assert_cptp(dv, label="drift weights")
    _pin_set(dv, _drift_ref("rz", 0.02, 0.08, [0.2, 0.5, 0.3]), atol=1e-12, label="drift weights")
    # wrong-length weights -> reset to default
    dl = drifted_axis_mixture_kraus("rx", epsilon=0.01, effective_span=0.05, weights=[1.0, 1.0])
    _pin_set(dl, _drift_ref("rx", 0.01, 0.05, [0.25, 0.5, 0.25]), atol=1e-12, label="drift badlen")
    # all-zero weights -> total<=0 -> reset to default
    dz = drifted_axis_mixture_kraus("rx", epsilon=0.01, effective_span=0.05, weights=[0.0, 0.0, 0.0])
    _pin_set(dz, _drift_ref("rx", 0.01, 0.05, [0.25, 0.5, 0.25]), atol=1e-12, label="drift zero")
    # negative span is abs()-ed (span = |effective_span|)
    dn = drifted_axis_mixture_kraus("rx", epsilon=0.01, effective_span=-0.05, weights=[0.25, 0.5, 0.25])
    _pin_set(dn, _drift_ref("rx", 0.01, 0.05, [0.25, 0.5, 0.25]), atol=1e-12, label="drift negspan")


def test_KILLER_drifted_axis_mixture_discriminates():
    # a mutant that dropped the +/- offset (pure mean rotation x3) is CPTP-equivalent to a plain
    # rotation mixture but is NOT the drift channel -> the pinned offsets discriminate.
    def wrong():
        w = [0.25, 0.5, 0.25]
        return [math.sqrt(x) * _rx(0.03) for x in w]   # no offsets
    assert_discriminates(lambda k: _pin_set(k, _drift_ref("rx", 0.03, 0.09, [0.25, 0.5, 0.25]), atol=1e-12),
                         drifted_axis_mixture_kraus("rx", epsilon=0.03, effective_span=0.09,
                                                    weights=[0.25, 0.5, 0.25]),
                         wrong(), label="drift offsets")


# =========================================================================== #
# leakage_channel_super + leakage_kraus (WG qutrit, scipy.expm)                #
# =========================================================================== #
def test_L0_leakage_channel_super_pinned_vs_independent_expm():
    # CONVERGENCE note: expm is EXACT (not a truncation); the generator is stated in _leak_super_ref.
    for theta, gs, gh in [(0.2, 0.05, 0.03), (0.15, 0.0, 0.0), (0.1, 0.08, 0.0), (0.0, 0.0, 0.06)]:
        S = leakage_channel_super(theta, gs, gh, t=1.0)
        _pin(S, _leak_super_ref(theta, gs, gh, 1.0), atol=1e-10, label="leak_super")
    # t scaling is honored (t=0 -> identity superop)
    _pin(leakage_channel_super(0.2, 0.05, 0.03, t=0.0), np.eye(9, dtype=np.complex128),
         atol=1e-10, label="leak_super t0")
    # theta=0,g_seep=0,g_heat=0 -> the 3x3 identity channel (no leakage)
    _pin(leakage_channel_super(0.0, 0.0, 0.0), np.eye(9, dtype=np.complex128), atol=1e-10, label="leak_super inert")


def test_L0_leakage_kraus_channel_level_pin_and_cptp():
    # the operator-sum form is basis-free (eigenbasis-dependent), so pin the CHANNEL: the superop
    # reconstructed from the returned Kraus MUST equal the independent expm channel.
    for theta, gs, gh in [(0.2, 0.05, 0.0), (0.2, 0.05, 0.03), (0.15, 0.0, 0.0)]:
        kr = leakage_kraus(theta, gs, gh)
        assert_cptp(kr, label="leak_kraus")
        _pin(_super_from_kraus(kr), _leak_super_ref(theta, gs, gh, 1.0), atol=1e-10, label="leak_kraus channel")
    # rank = kept Kraus count (eigenvalues > tol dropped) -> coherent-leakage channel is rank 5
    assert len(leakage_kraus(0.2, 0.05, 0.0)) == 5
    # |0> is inert: E(|0><0|) = |0><0| (the {|0>,|1>} restriction is identity at theta=g=0)
    kr0 = leakage_kraus(0.0, 0.0, 0.0)
    rho0 = _qop(0, 0)
    out = sum(K @ rho0 @ K.conj().T for K in kr0)
    _pin(out, rho0, atol=1e-10, label="leak |0> inert")


def test_KILLER_leakage_channel_discriminates():
    # a different coherent strength is still a valid CPTP leakage channel but a different one
    assert_discriminates(lambda S: _pin(S, _leak_super_ref(0.2, 0.05, 0.0, 1.0), atol=1e-10),
                         leakage_channel_super(0.2, 0.05, 0.0),
                         leakage_channel_super(0.35, 0.05, 0.0), label="leak_super")


# =========================================================================== #
# readout_bias_matrix                                                         #
# =========================================================================== #
def test_L0_readout_bias_matrix_pinned_row_stochastic():
    for p01, p10 in [(0.02, 0.01), (0.0, 0.0), (0.1, 0.3)]:
        m = readout_bias_matrix(p0_to_1=p01, p1_to_0=p10)
        assert_row_stochastic(m, label="readout")
        assert_pins(m.ravel(), _readout(p01, p10).ravel(), atol=1e-12, label="readout")
    # asymmetric so a p01<->p10 transpose diverges; also pins the exact [[1-p01,p01],[p10,1-p10]] layout
    m = readout_bias_matrix(p0_to_1=0.1, p1_to_0=0.3)
    assert m[0, 1] == pytest.approx(0.1) and m[1, 0] == pytest.approx(0.3)
    assert m[0, 0] == pytest.approx(0.9) and m[1, 1] == pytest.approx(0.7)


def test_KILLER_readout_bias_matrix_discriminates():
    assert_discriminates(lambda m: assert_pins(m.ravel(), _readout(0.1, 0.3).ravel(), atol=1e-12),
                         readout_bias_matrix(p0_to_1=0.1, p1_to_0=0.3),
                         readout_bias_matrix(p0_to_1=0.3, p1_to_0=0.1), label="readout")


# =========================================================================== #
# canonical_single_qubit_axis                                                 #
# =========================================================================== #
def test_L0_canonical_single_qubit_axis_all_paths():
    # aliases (x/rx, y/ry, z/rz) + strip/lower normalization
    assert canonical_single_qubit_axis("x") == "rx"
    assert canonical_single_qubit_axis("RX") == "rx"
    assert canonical_single_qubit_axis(" Y ") == "ry"
    assert canonical_single_qubit_axis("ry") == "ry"
    assert canonical_single_qubit_axis("z") == "rz"
    assert canonical_single_qubit_axis("rz") == "rz"
    # None -> default; custom default honored
    assert canonical_single_qubit_axis(None) == "rx"
    assert canonical_single_qubit_axis(None, default="rz") == "rz"
    # invalid -> exact message
    with pytest.raises(ValueError) as e:
        canonical_single_qubit_axis("w")
    assert str(e.value) == "single-qubit rotation axis must be one of x/rx, y/ry, or z/rz"


# =========================================================================== #
# mechanism_operation_axis / mechanism_error_axis                             #
# =========================================================================== #
def _spec(mid, params=None, *, nq=1, instruction=None):
    return MechanismSpec(mid, "name", nq, dict(params or {}), instruction=instruction)


def test_L0_mechanism_operation_axis_paths():
    # non-M14: operation_axis param wins, else axis, else instruction default
    assert mechanism_operation_axis(_spec("M6", {"operation_axis": "ry"})) == "ry"
    assert mechanism_operation_axis(_spec("M6", {"axis": "z"})) == "rz"
    assert mechanism_operation_axis(_spec("M6", instruction="ry")) == "ry"
    assert mechanism_operation_axis(_spec("M6")) == "rx"          # default fallback
    # M14 also consults 'instruction' param key (distinct branch) + the 'axis' fallback key
    assert mechanism_operation_axis(_spec("M14", {"instruction": "rz"})) == "rz"
    assert mechanism_operation_axis(_spec("M14", {"operation_axis": "ry"})) == "ry"
    assert mechanism_operation_axis(_spec("M14", {"axis": "ry"})) == "ry"   # 'axis' fallback key
    assert mechanism_operation_axis(_spec("M14")) == "rx"                   # default fallback
    # M14 with a non-rx INSTRUCTION attribute + no params -> the innermost `default` (from the
    # instruction) is load-bearing; a mutated `params.get("axis", None)` falls to canonical's own
    # "rx" != "ry", so this kills the axis-fallback-default mutation in the M14 branch.
    assert mechanism_operation_axis(_spec("M14", instruction="ry")) == "ry"
    # EXPLICIT-None value: MechanismSpec has NO __post_init__ so parameters={"operation_axis": None}
    # is constructible; params.get returns None (key PRESENT -> the fallback is NOT taken) -> value=None
    # -> the `canonical_single_qubit_axis(..., default="rx")` default arg is LIVE. instruction="rz"
    # gives a DIFFERENT fall-through ("rz"), so asserting "rx" proves the default="rx" arg (not the
    # fall-through) is used -> kills the default="XXrxXX" WRAP + default=None mutants on BOTH the
    # non-M14 and M14 branches. (The default="RX" CASE mutant stays equivalent -- canonical .lower()s.)
    assert mechanism_operation_axis(_spec("M1", {"operation_axis": None}, instruction="rz")) == "rx"
    assert mechanism_operation_axis(_spec("M14", {"operation_axis": None}, instruction="rz")) == "rx"


def test_L0_mechanism_error_axis_paths_and_m13_guard():
    # M14: error_axis / channel_axis, default rz (error_axis value != default so the KEY matters)
    assert mechanism_error_axis(_spec("M14", {"error_axis": "ry"})) == "ry"
    assert mechanism_error_axis(_spec("M14", {"channel_axis": "ry"})) == "ry"
    assert mechanism_error_axis(_spec("M14")) == "rz"          # both absent -> value=None -> "rz" default
    # non-M14 non-M13: error axis == operation axis
    assert mechanism_error_axis(_spec("M6", {"operation_axis": "ry"})) == "ry"
    # M13: channel axis must MATCH operation axis (default) -> returns it
    assert mechanism_error_axis(_spec("M13", {"operation_axis": "rx"})) == "rx"
    # M13 EXPLICIT error_axis=None with a NON-rx operation_axis: value=None -> the
    # `canonical_single_qubit_axis(..., default=operation_axis)` arg is LIVE (returns operation_axis).
    # operation_axis="rz" so a mutated default is observable: default=None -> canonical(None,None) raises;
    # default REMOVED -> canonical's own "rx" != "rz" -> the `requested != operation` guard raises.
    # Either way the call raises while orig returns "rz", so this kills the M13 default-arg mutants.
    assert mechanism_error_axis(_spec("M13", {"operation_axis": "rz", "error_axis": None})) == "rz"
    # M13: a MISMATCHED channel axis raises with the exact message -- via the EXPLICIT error_axis route
    with pytest.raises(ValueError) as e:
        mechanism_error_axis(_spec("M13", {"operation_axis": "rx", "error_axis": "rz"}))
    assert str(e.value) == "M13 drifted coherent overrotation requires channel axis to match operation_axis"
    # ...AND via the channel_axis FALLBACK route (error_axis ABSENT so the value routes through
    # `params.get("channel_axis", operation_axis)`). A guard that raises must be tripped through EVERY
    # input route into it: the channel_axis-lookup mutants (wrong key / dropped default) would resolve
    # `value` to operation_axis instead of the mismatched "rx", suppressing THIS raise -> they are
    # killed only by exercising the mismatch on the channel_axis path (not the error_axis path).
    with pytest.raises(ValueError) as e2:
        mechanism_error_axis(_spec("M13", {"operation_axis": "rz", "channel_axis": "rx"}))
    assert str(e2.value) == "M13 drifted coherent overrotation requires channel axis to match operation_axis"


# =========================================================================== #
# mechanism_definition_contract                                               #
# =========================================================================== #
def test_L0_definition_contract_M13_full_dict():
    params = {"operation_axis": "rx", "epsilon": 0.031, "epsilon_mean": 0.033,
              "epsilon_span": 0.02, "drift_visibility_scale": 4.0, "drift_mixture_weights": [0.2, 0.5, 0.3]}
    c = mechanism_definition_contract(_spec("M13", params, instruction="rx"))
    expected = {
        "mechanism_id": "M13",
        "formal_name": "drifted_coherent_overrotation",
        "definition": "context-dependent coherent overrotation attached to the declared operation axis, represented as a row-visible drift mixture",
        "contract_role": "context_conditioned_family",
        "operation_axis": "rx", "channel_axis": "rx", "error_axis": "rx",
        "drift_parameter": "epsilon",
        "epsilon": 0.031, "epsilon_mean": 0.033, "epsilon_span": 0.02,
        "drift_visibility_scale": 4.0, "effective_epsilon_span": 0.08,
        "angle_offsets": [-0.08, 0.0, 0.08], "mixture_weights": [0.2, 0.5, 0.3],
        "channel_representation": "random_unitary_kraus_mixture",
        "drift_overlay_payload_present": True,
        "row_level_visible_geometry": "mean_rotation_plus_drift_mixture_curvature",
        "context_dependent": True, "operation_dependent": False,
        "single_context_exact_recovery_required": False,
        "claims_standalone_flat_mechanism": False, "well_defined": True,
    }
    assert c == expected


def test_L0_definition_contract_M13_inert_span_is_unitary_representation():
    # drift_visibility_scale 0 -> effective_span 0 -> channel_representation 'unitary'
    c = mechanism_definition_contract(_spec("M13", {"operation_axis": "rx", "drift_visibility_scale": 0.0},
                                            instruction="rx"))
    assert c["effective_epsilon_span"] == 0.0
    assert c["channel_representation"] == "unitary"
    assert c["drift_overlay_payload_present"] is False
    assert c["angle_offsets"] == [0.0] and c["mixture_weights"] == [1.0]


def test_L0_definition_contract_M14_full_dict_and_well_defined_flag():
    # epsilon 0.05 != the 0.028 default so the "epsilon" KEY is load-bearing here
    c = mechanism_definition_contract(_spec("M14", {"operation_axis": "rx", "error_axis": "rz",
                                                    "epsilon": 0.05}))
    assert c == {
        "mechanism_id": "M14",
        "formal_name": "operation_dependent_error",
        "definition": "coherent error generator attached to a visible operation axis",
        "operation_axis": "rx", "channel_axis": "rz", "error_axis": "rz",
        "epsilon": 0.05, "context_dependent": False, "operation_dependent": True,
        "distinct_from_axis_overrotation": True, "well_defined": True,
    }
    # when channel axis EQUALS operation axis -> not distinct, not well_defined
    c2 = mechanism_definition_contract(_spec("M14", {"operation_axis": "rz", "error_axis": "rz"}))
    assert c2["distinct_from_axis_overrotation"] is False and c2["well_defined"] is False
    assert c2["epsilon"] == 0.028  # default epsilon when absent


def test_L0_definition_contract_M11_two_and_one_qubit_and_default():
    c2 = mechanism_definition_contract(_spec("M11", {"epsilon": 0.02}, nq=2))
    assert c2["sampling_surrogate"]["carrier_channel"] == "rzz_unitary"
    assert c2 == {
        "mechanism_id": "M11", "formal_name": "spectator_crosstalk_overlay",
        "definition": "non-flat spectator overlay represented scientifically as base_mechanism plus spectator_overlay metadata",
        "contract_role": "overlay_family", "overlay_family": "spectator_crosstalk",
        "sampling_surrogate": {"carrier_channel": "rzz_unitary",
                               "claims_exact_physical_overlay_channel": False,
                               "claims_standalone_flat_mechanism": False},
        "leaf_exact_effect_supported": False, "primary_flat_cluster_target": False, "well_defined": True,
    }
    c1 = mechanism_definition_contract(_spec("M11", {"epsilon": 0.02}, nq=1))
    assert c1["sampling_surrogate"]["carrier_channel"] == "rz_unitary"
    # a plain (non-M11/13/14) mechanism -> minimal contract
    d = mechanism_definition_contract(MechanismSpec("M5", "dephase", 1, {}, instruction="id"))
    assert d == {"mechanism_id": "M5", "formal_name": "dephase", "instruction": "id", "well_defined": True}


# =========================================================================== #
# MechanismSpec.audit_dict                                                     #
# =========================================================================== #
def test_L0_audit_dict_plain_mechanism_full():
    spec = MechanismSpec("M5", "dephase", 1, {"p_z": 0.0025}, instruction="id",
                         qubits=(0,), circuit_id=3, probe_indices=(1, 2))
    ad = spec.audit_dict()
    assert ad == {
        "legacy_catalog_id": "M5", "public_label": "F1", "label_namespace": "flat",
        "mechanism_id": "M5", "name": "dephase", "num_qubits": 1,
        "parameters": {"p_z": 0.0025}, "instruction": "id",
        "qubits": [0], "circuit_id": 3, "probe_indices": [1, 2],
    }


def test_L0_audit_dict_json_value_branches():
    # _json_value: basic types pass through; a numpy scalar -> float(); a non-floatable -> str()
    class _Obj:
        def __repr__(self): return "OBJ"
    spec = MechanismSpec("M5", "n", 1, {"i": 3, "f": 1.5, "s": "t", "b": True, "n": None,
                                        "np": np.float64(2.5), "o": _Obj()})
    p = spec.audit_dict()["parameters"]
    assert p["i"] == 3 and p["f"] == 1.5 and p["s"] == "t" and p["b"] is True and p["n"] is None
    assert p["np"] == 2.5 and isinstance(p["np"], float)
    assert p["o"] == "OBJ"


def test_L0_audit_dict_M11_overlay_present_and_absent():
    present = MechanismSpec("M11", "spec", 2, {
        "epsilon": 0.02, "spectator_overlay_present": True, "base_mechanism": "M8",
        "victim_relative_location": "edge", "aggressor_relative_location": "adjacent_gate",
        "coupling_axis": "ZZ", "timing_context": "same_cycle", "spectator_strength": 0.02,
        "victim_qubit": 1, "aggressor_qubit": 2}, instruction="rzz", qubits=(1, 2))
    ad = present.audit_dict()
    assert ad["contract_role"] == "overlay_family"
    assert ad["overlay_family"] == "spectator_crosstalk"
    assert ad["public_effect_family"] == "spectator_overlay"
    assert ad["public_overlay_class"] == "M6_overlay"          # public_label M6
    assert ad["nonflat_public_label"] == "spectator_overlay_M6"
    assert ad["spectator_overlay_present"] is True
    assert ad["base_mechanism"] == "M8" and ad["coupling_axis"] == "ZZ"
    assert ad["timing_context"] == "same_cycle" and ad["spectator_strength"] == 0.02
    assert ad["victim_qubit"] == 1 and ad["aggressor_qubit"] == 2
    assert ad["spectator_overlay"]["present"] is True
    assert ad["spectator_overlay"]["base_mechanism"] == "M8"
    assert ad["claims_standalone_flat_mechanism"] is False
    # overlay ABSENT (spectator_overlay_present missing) -> no overlay keys merged
    absent = MechanismSpec("M11", "spec", 2, {"epsilon": 0.02}, instruction="rzz", qubits=(1, 2))
    ada = absent.audit_dict()
    assert "contract_role" not in ada and "spectator_overlay" not in ada
    # a present overlay WITHOUT victim/aggressor qubits omits those keys (their `if ... is not None`)
    noq = MechanismSpec("M11", "spec", 2, {"epsilon": 0.02, "spectator_overlay_present": True,
                                           "base_mechanism": "M8"}, instruction="rzz", qubits=(1, 2))
    adn = noq.audit_dict()
    assert "victim_qubit" not in adn and "aggressor_qubit" not in adn
    assert adn["spectator_overlay_present"] is True


def test_L0_audit_dict_M13_drift_overlay():
    spec = MechanismSpec("M13", "spec", 1, {"operation_axis": "rx", "epsilon": 0.035,
                                            "epsilon_span": 0.018}, instruction="rx", qubits=(0,))
    ad = spec.audit_dict()
    assert ad["contract_role"] == "context_conditioned_family"
    assert ad["public_effect_family"] == "context_conditioned_drift"
    assert ad["public_overlay_class"] == "M7_drift_overlay"     # public_label M7
    assert ad["nonflat_public_label"] == "context_conditioned_drift_M7"
    assert ad["drift_overlay_present"] is True
    assert ad["operation_axis"] == "rx" and ad["channel_axis"] == "rx"
    assert ad["drift_strength"] == pytest.approx(0.018 * 5.0)
    assert ad["single_context_exact_recovery_required"] is False
    ov = ad["drift_overlay"]
    assert ov["present"] is True
    assert ov["channel_representation"] == "random_unitary_kraus_mixture"
    assert ov["angle_offsets"] == [-0.09, 0.0, 0.09]
    assert ov["mixture_weights"] == [0.25, 0.5, 0.25]
    assert ov["effective_epsilon_span"] == pytest.approx(0.09)


# =========================================================================== #
# mechanism_channel -- full dispatch at DEFAULT params (kills mutated defaults) #
# =========================================================================== #
def _mk(mid, *, nq=1, instruction="id", params=None, qubits=None):
    q = qubits if qubits is not None else tuple(range(nq))
    return MechanismSpec(mid, "name", nq, dict(params or {}), instruction=instruction, qubits=q)


def test_L0_mechanism_channel_unitary_mechanisms_at_defaults():
    cases = {
        "M6": ("rx", _rx(0.035), 1), "M7": ("rz", _rz(0.035), 1), "M18": ("rx", _rx(0.025), 1),
        "M20": ("ry", _ry(0.03), 1), "M8": ("rzz", _rzz(0.04), 2), "M22": ("rxx", _rxx(0.022), 2),
        "M23": ("ryy", _ryy(0.019), 2), "M21": ("cphase", _cphase(0.035), 2),
        "M10": ("rxx_ryy", _ryy(0.0175) @ _rxx(0.025), 2),
        "M27": ("single", _single_axis(0.026, {"X": 1.0, "Z": 1.0}), 1),
        "M28": ("tp", _two_pauli(0.015, "X", "Y"), 2), "M29": ("tp", _two_pauli(0.018, "Z", "X"), 2),
        "M30": ("tp", _two_pauli(0.016, "Z", "Y"), 2), "M31": ("tp", _two_pauli(0.017, "X", "Z"), 2),
        "M32": ("tp", _two_pauli(0.014, "Y", "Z"), 2), "M33": ("tp", _two_pauli(0.013, "Y", "X"), 2),
    }
    for mid, (_, ref, nq) in cases.items():
        ch_out = mechanism_channel(_mk(mid, nq=nq, instruction=("rzz" if nq == 2 else "id")))
        assert ch_out["kind"] == "unitary", mid
        _pin(ch_out["unitary"], ref, atol=1e-11, label=f"channel {mid}")


def test_L0_mechanism_channel_kraus_mechanisms_at_defaults():
    assert_and_pin = lambda mid, nq, ref, instr="id": _check_kraus(mid, nq, ref, instr)
    _check_kraus("M0", 1, _pauli_stoch({"X": 0.002 / 3.0, "Y": 0.002 / 3.0, "Z": 0.002 / 3.0}))
    _check_kraus("M4", 1, _amp(0.015))
    _check_kraus("M5", 1, _pauli_stoch({"Z": 0.0025}))
    _check_kraus("M9", 2, _two_qubit_depol(0.006), "rzz")
    _check_kraus("M12", 2, _corr_relax(0.01), "rzz")
    _check_kraus("M15", 1, _custom_non_pauli(0.02))
    _check_kraus("M17", 1, _reset(0.018, 1))
    _check_kraus("M19", 1, _weak_type4(0.006))
    _check_kraus("M24", 1, _thermal_exc(0.006))
    _check_kraus("M25", 1, _pauli_stoch({"X": 0.006}))
    _check_kraus("M26", 1, _pauli_stoch({"Y": 0.006}))
    _check_kraus("M34", 1, _leak_surrogate(0.004))


def _check_kraus(mid, nq, ref, instr="id"):
    out = mechanism_channel(_mk(mid, nq=nq, instruction=instr))
    assert out["kind"] == "kraus", mid
    _pin_set(out["kraus"], ref, atol=1e-11, label=f"channel {mid}")


def test_L0_mechanism_channel_readout_mechanisms_at_defaults():
    cases = {"M1": _readout(0.02, _NZ), "M2": _readout(_NZ, 0.02),
             "M3": _readout(0.02, 0.02), "M16": _readout(0.02, 0.5 * 0.02)}
    for mid, ref in cases.items():
        out = mechanism_channel(_mk(mid, nq=1, instruction="measure"))
        assert out["kind"] == "readout", mid
        assert_pins(np.asarray(out["matrix"]).ravel(), ref.ravel(), atol=1e-12, label=f"readout {mid}")


def test_L0_mechanism_channel_M11_two_and_one_qubit():
    out2 = mechanism_channel(_mk("M11", nq=2, instruction="rzz", params={"epsilon": 0.02}))
    assert out2["kind"] == "unitary"
    _pin(out2["unitary"], _rzz(0.02), atol=1e-12, label="M11 2q")
    assert out2["definition_contract"]["contract_role"] == "overlay_family"
    # 1q branch: assert EVERY return-dict key (kind/unitary/definition_contract) so a key/value
    # mutation on that return line is caught (not just the unitary matrix).
    out1 = mechanism_channel(_mk("M11", nq=1, instruction="id", params={"epsilon": 0.02}))
    assert out1["kind"] == "unitary"
    _pin(out1["unitary"], _rz(0.02), atol=1e-12, label="M11 1q")
    assert out1["definition_contract"]["contract_role"] == "overlay_family"
    # EMPTY params exercise the 0.02 DEFAULT on BOTH return lines (kills the default-constant mutation)
    e2 = mechanism_channel(_mk("M11", nq=2, instruction="rzz"))
    assert e2["kind"] == "unitary"
    _pin(e2["unitary"], _rzz(0.02), atol=1e-12, label="M11 2q default")
    assert e2["definition_contract"]["contract_role"] == "overlay_family"
    e1 = mechanism_channel(_mk("M11", nq=1, instruction="id"))
    assert e1["kind"] == "unitary"
    _pin(e1["unitary"], _rz(0.02), atol=1e-12, label="M11 1q default")
    assert e1["definition_contract"]["contract_role"] == "overlay_family"


def test_L0_mechanism_channel_M13_kraus_and_unitary_branches():
    # default M13 -> drift mixture (kraus)
    outk = mechanism_channel(_mk("M13", nq=1, instruction="rx", params={"operation_axis": "rx"}))
    assert outk["kind"] == "kraus"
    _pin_set(outk["kraus"], _drift_ref("rx", 0.03, 0.09, [0.25, 0.5, 0.25]), atol=1e-11, label="M13 kraus")
    assert outk["definition_contract"]["drift_overlay_payload_present"] is True
    # inert drift (effective_span 0) -> plain axis unitary
    outu = mechanism_channel(_mk("M13", nq=1, instruction="rx",
                                 params={"operation_axis": "rx", "drift_visibility_scale": 0.0}))
    assert outu["kind"] == "unitary"
    _pin(outu["unitary"], _rx(0.03), atol=1e-12, label="M13 unitary")


def test_L0_mechanism_channel_M14_and_unknown_raise():
    # explicit epsilon 0.05 (!= 0.028 default -> the "epsilon" key matters)
    out = mechanism_channel(_mk("M14", nq=1, instruction="rx",
                                params={"operation_axis": "rx", "error_axis": "rz", "epsilon": 0.05}))
    assert out["kind"] == "unitary"
    _pin(out["unitary"], _rz(0.05), atol=1e-12, label="M14")
    assert out["definition_contract"]["operation_dependent"] is True
    # empty params -> the 0.028 default + rz error-axis default (kills the default constant)
    oute = mechanism_channel(_mk("M14", nq=1, instruction="rx"))
    _pin(oute["unitary"], _rz(0.028), atol=1e-12, label="M14 default")
    # unknown mechanism id -> exact raise
    with pytest.raises(ValueError) as e:
        mechanism_channel(_mk("M99", nq=1))
    assert str(e.value) == "unknown physical mechanism id 'M99'"


def test_L0_mechanism_channel_M0_explicit_and_readout_membership():
    # M0 explicit per-axis probs (pins the p_x/p_y/p_z routing)
    out = mechanism_channel(_mk("M0", nq=1, params={"p_x": 0.001, "p_y": 0.002, "p_z": 0.003}))
    _pin_set(out["kraus"], _pauli_stoch({"X": 0.001, "Y": 0.002, "Z": 0.003}), atol=1e-12, label="M0 explicit")
    # M0 with a single 'p' -> split p/3 across axes
    out2 = mechanism_channel(_mk("M0", nq=1, params={"p": 0.009}))
    _pin_set(out2["kraus"], _pauli_stoch({"X": 0.003, "Y": 0.003, "Z": 0.003}), atol=1e-12, label="M0 p")
    # M16 uses p1_to_0 = 0.5*p (distinct from M1/M2/M3) -- pins the `if mech == "M16"` branch
    m16 = mechanism_channel(_mk("M16", nq=1, instruction="measure", params={"p": 0.04}))
    assert_pins(np.asarray(m16["matrix"]).ravel(), _readout(0.04, 0.02).ravel(), atol=1e-12, label="M16 p")


def test_KILLER_mechanism_channel_discriminates():
    # M6 (rx) vs a plausible wrong dispatch to rz -- both unitary, different channel
    assert_discriminates(lambda o: _pin(o["unitary"], _rx(0.035), atol=1e-11),
                         mechanism_channel(_mk("M6", nq=1)),
                         {"kind": "unitary", "unitary": _rz(0.035)}, label="M6 dispatch")


# =========================================================================== #
# mechanism_channel -- EXPLICIT non-default params (kills the params.get KEY-  #
# string mutations that the empty-params pass leaves as equivalents)          #
# =========================================================================== #
def test_L0_mechanism_channel_explicit_nondefault_unitary_params():
    # each value is chosen DISTINCT from the mechanism's default so the get() KEY is load-bearing:
    # a mutated key (or None) falls back to the default != the supplied value -> pin diverges.
    cases = [
        ("M6", 1, {"epsilon": 0.1}, _rx(0.1)),
        ("M7", 1, {"epsilon": 0.1}, _rz(0.1)),
        ("M8", 2, {"epsilon": 0.1}, _rzz(0.1)),
        ("M18", 1, {"epsilon": 0.05}, _rx(0.05)),
        ("M20", 1, {"epsilon": 0.05}, _ry(0.05)),
        ("M21", 2, {"epsilon": 0.05}, _cphase(0.05)),
        ("M22", 2, {"epsilon": 0.05}, _rxx(0.05)),
        ("M23", 2, {"epsilon": 0.05}, _ryy(0.05)),
        ("M27", 1, {"epsilon": 0.05}, _single_axis(0.05, {"X": 1.0, "Z": 1.0})),
        ("M28", 2, {"epsilon": 0.05}, _two_pauli(0.05, "X", "Y")),
        ("M29", 2, {"epsilon": 0.05}, _two_pauli(0.05, "Z", "X")),
        ("M30", 2, {"epsilon": 0.05}, _two_pauli(0.05, "Z", "Y")),
        ("M31", 2, {"epsilon": 0.05}, _two_pauli(0.05, "X", "Z")),
        ("M32", 2, {"epsilon": 0.05}, _two_pauli(0.05, "Y", "Z")),
        ("M33", 2, {"epsilon": 0.05}, _two_pauli(0.05, "Y", "X")),
    ]
    for mid, nq, params, ref in cases:
        out = mechanism_channel(_mk(mid, nq=nq, instruction=("rzz" if nq == 2 else "id"), params=params))
        assert out["kind"] == "unitary", mid
        _pin(out["unitary"], ref, atol=1e-11, label=f"{mid} explicit")
    # M10: two DISTINCT explicit angles pin BOTH keys epsilon_x/epsilon_y; a single 'epsilon' pins
    # the inner fallback key + the *0.7 factor.
    m10 = mechanism_channel(_mk("M10", nq=2, instruction="rzz", params={"epsilon_x": 0.05, "epsilon_y": 0.03}))
    _pin(m10["unitary"], _ryy(0.03) @ _rxx(0.05), atol=1e-11, label="M10 xy")
    m10e = mechanism_channel(_mk("M10", nq=2, instruction="rzz", params={"epsilon": 0.06}))
    _pin(m10e["unitary"], _ryy(0.06 * 0.7) @ _rxx(0.06), atol=1e-11, label="M10 epsilon+0.7")
    # M11 explicit epsilon (0.05 != 0.02 default), both arities
    _pin(mechanism_channel(_mk("M11", nq=2, instruction="rzz", params={"epsilon": 0.05}))["unitary"],
         _rzz(0.05), atol=1e-12, label="M11 2q explicit")
    _pin(mechanism_channel(_mk("M11", nq=1, instruction="id", params={"epsilon": 0.05}))["unitary"],
         _rz(0.05), atol=1e-12, label="M11 1q explicit")


def test_L0_mechanism_channel_explicit_nondefault_kraus_params():
    _check_kraus_p("M4", 1, {"gamma": 0.2}, _amp(0.2))
    _check_kraus_p("M5", 1, {"p_z": 0.01}, _pauli_stoch({"Z": 0.01}))
    _check_kraus_p("M5", 1, {"p": 0.008}, _pauli_stoch({"Z": 0.008}))       # inner 'p' fallback key
    _check_kraus_p("M9", 2, {"p": 0.05}, _two_qubit_depol(0.05), "rzz")
    _check_kraus_p("M12", 2, {"gamma": 0.05}, _corr_relax(0.05), "rzz")
    _check_kraus_p("M15", 1, {"eta": 0.05}, _custom_non_pauli(0.05))
    _check_kraus_p("M17", 1, {"p": 0.05}, _reset(0.05, 1))
    _check_kraus_p("M19", 1, {"eta": 0.05}, _weak_type4(0.05))
    _check_kraus_p("M24", 1, {"gamma_up": 0.05}, _thermal_exc(0.05))
    _check_kraus_p("M24", 1, {"p": 0.04}, _thermal_exc(0.04))               # inner 'p' fallback key
    _check_kraus_p("M25", 1, {"p": 0.05}, _pauli_stoch({"X": 0.05}))
    _check_kraus_p("M26", 1, {"p": 0.05}, _pauli_stoch({"Y": 0.05}))
    _check_kraus_p("M34", 1, {"p": 0.05}, _leak_surrogate(0.05))


def _check_kraus_p(mid, nq, params, ref, instr="id"):
    out = mechanism_channel(_mk(mid, nq=nq, instruction=instr, params=params))
    assert out["kind"] == "kraus", mid
    _pin_set(out["kraus"], ref, atol=1e-11, label=f"{mid} explicit")


def test_L0_mechanism_channel_readout_explicit_keys():
    # explicit p != 0.02 default -> the 'p' key + the membership sets {M1,M3,M16}/{M2,M3} matter
    for mid, ref in [("M1", _readout(0.05, _NZ)), ("M2", _readout(_NZ, 0.05)),
                     ("M3", _readout(0.05, 0.05))]:
        m = mechanism_channel(_mk(mid, nq=1, instruction="measure", params={"p": 0.05}))
        assert_pins(np.asarray(m["matrix"]).ravel(), ref.ravel(), atol=1e-12, label=f"{mid} p")
    # explicit p0_to_1 / p1_to_0 override keys (kills the params.get("p0_to_1"/"p1_to_0") keys)
    m = mechanism_channel(_mk("M1", nq=1, instruction="measure",
                              params={"p0_to_1": 0.07, "p1_to_0": 0.03}))
    assert_pins(np.asarray(m["matrix"]).ravel(), _readout(0.07, 0.03).ravel(), atol=1e-12, label="readout override")


def test_L0_mechanism_channel_M13_explicit_axis_and_weights():
    # op_axis 'rz' (!= rx default) kills axis=None; epsilon 0.05 (!= 0.03) kills the angle key;
    # custom weights [0.2,0.5,0.3] (!= [0.25,0.5,0.25]) kill weights=None + the "mixture_weights" key.
    p = {"operation_axis": "rz", "epsilon": 0.05, "epsilon_span": 0.02, "drift_visibility_scale": 4.0,
         "drift_mixture_weights": [0.2, 0.5, 0.3]}
    out = mechanism_channel(_mk("M13", nq=1, instruction="rz", params=p))
    assert out["kind"] == "kraus"
    _pin_set(out["kraus"], _drift_ref("rz", 0.05, 0.08, [0.2, 0.5, 0.3]), atol=1e-11, label="M13 rz kraus")
    assert out["definition_contract"]["channel_axis"] == "rz"
    # inert branch with op_axis rz: unitary must be rz(0.05), and definition_contract key is accessed
    pu = {"operation_axis": "rz", "epsilon": 0.05, "drift_visibility_scale": 0.0}
    outu = mechanism_channel(_mk("M13", nq=1, instruction="rz", params=pu))
    assert outu["kind"] == "unitary"
    _pin(outu["unitary"], _rz(0.05), atol=1e-12, label="M13 rz unitary")
    assert outu["definition_contract"]["contract_role"] == "context_conditioned_family"


# =========================================================================== #
# MechanismSpec.audit_dict -- FULL M11/M13 overlay dicts (every key + value)   #
# so a string-KEY or value mutation in the private overlay builders diverges.  #
# =========================================================================== #
def test_L0_audit_dict_M11_full_overlay_dict_and_alias_fallbacks():
    p = {"epsilon": 0.02, "spectator_overlay_present": True, "base_mechanism": "M8",
         "victim_relative_location": "edge", "aggressor_relative_location": "adjacent_gate",
         "coupling_axis": "ZZ", "timing_context": "same_cycle", "spectator_strength": 0.021,
         "victim_qubit": 1, "aggressor_qubit": 2, "claims_standalone_flat_mechanism": True}
    ad = MechanismSpec("M11", "spec", 2, p, instruction="rzz", qubits=(1, 2)).audit_dict()
    # every merged overlay key + value pinned (public_label M11->M6)
    assert ad["contract_role"] == "overlay_family"
    assert ad["overlay_family"] == "spectator_crosstalk"
    assert ad["public_effect_family"] == "spectator_overlay"
    assert ad["public_overlay_class"] == "M6_overlay"
    assert ad["nonflat_public_label"] == "spectator_overlay_M6"
    assert ad["spectator_overlay_present"] is True
    assert ad["base_mechanism"] == "M8"
    assert ad["victim_relative_location"] == "edge"
    assert ad["aggressor_relative_location"] == "adjacent_gate"
    assert ad["coupling_axis"] == "ZZ"
    assert ad["timing_context"] == "same_cycle"
    assert ad["spectator_strength"] == 0.021
    assert ad["victim_qubit"] == 1
    assert ad["aggressor_qubit"] == 2
    assert ad["claims_standalone_flat_mechanism"] is True     # kills the claims key + default False
    # the nested spectator_overlay sub-dict: EVERY key routed to its value
    ov = ad["spectator_overlay"]
    assert ov == {"present": True, "base_mechanism": "M8", "victim_relative_location": "edge",
                  "aggressor_relative_location": "adjacent_gate", "coupling_axis": "ZZ",
                  "timing_context": "same_cycle", "spectator_strength": 0.021,
                  "victim_qubit": 1, "aggressor_qubit": 2}
    # _first_present alias fallbacks: 'strength' and 'coupling_strength' picked when spectator_strength absent
    a2 = MechanismSpec("M11", "s", 2, {"spectator_overlay_present": True, "base_mechanism": "M8",
                                       "strength": 0.033}, instruction="rzz", qubits=(1, 2)).audit_dict()
    assert a2["spectator_strength"] == 0.033
    a3 = MechanismSpec("M11", "s", 2, {"spectator_overlay_present": True, "base_mechanism": "M8",
                                       "coupling_strength": 0.044}, instruction="rzz", qubits=(1, 2)).audit_dict()
    assert a3["spectator_strength"] == 0.044


def test_L0_audit_dict_M13_full_drift_overlay_dict():
    p = {"operation_axis": "rx", "epsilon": 0.035, "epsilon_mean": 0.037, "epsilon_span": 0.018}
    ad = MechanismSpec("M13", "spec", 1, p, instruction="rx", qubits=(0,)).audit_dict()
    assert ad["public_overlay_class"] == "M7_drift_overlay"       # public_label M7
    assert ad["nonflat_public_label"] == "context_conditioned_drift_M7"
    assert ad["public_effect_family"] == "context_conditioned_drift"
    assert ad["drift_overlay_present"] is True
    assert ad["drift_strength"] == pytest.approx(0.018 * 5.0)
    # the nested drift_overlay: EVERY key + value pinned (epsilon/epsilon_mean/span distinct)
    ov = ad["drift_overlay"]
    assert ov["present"] is True
    assert ov["operation_axis"] == "rx"
    assert ov["channel_axis"] == "rx"
    assert ov["epsilon"] == 0.035
    assert ov["epsilon_mean"] == 0.037
    assert ov["epsilon_span"] == 0.018
    assert ov["drift_visibility_scale"] == 5.0
    assert ov["effective_epsilon_span"] == pytest.approx(0.09)
    assert ov["angle_offsets"] == [-0.09, 0.0, 0.09]
    assert ov["mixture_weights"] == [0.25, 0.5, 0.25]
    assert ov["channel_representation"] == "random_unitary_kraus_mixture"
    # the fixed "claims_standalone_flat_mechanism": False key+value (kills its key/value mutations)
    assert ad["claims_standalone_flat_mechanism"] is False


def test_L0_audit_dict_M13_inert_drift_overlay_present_flag_is_false():
    # effective_span == 0 -> present / drift_overlay_present must be FALSE (kills `> 0` -> `>= 0`)
    p = {"operation_axis": "rx", "drift_visibility_scale": 0.0}
    ad = MechanismSpec("M13", "spec", 1, p, instruction="rx", qubits=(0,)).audit_dict()
    assert ad["drift_overlay_present"] is False
    assert ad["drift_overlay"]["present"] is False
    assert ad["drift_overlay"]["channel_representation"] == "unitary"


# =========================================================================== #
# mechanism_definition_contract -- drift-span alias + epsilon/mean routing     #
# =========================================================================== #
def test_L0_definition_contract_M13_drift_span_alias_and_epsilon_mean_routing():
    # 'drift_span' alias feeds epsilon_span when 'epsilon_span' is absent (kills the drift_span key/abs)
    c = mechanism_definition_contract(_spec("M13", {"operation_axis": "rx", "drift_span": 0.03,
                                                    "drift_visibility_scale": 2.0}, instruction="rx"))
    assert c["epsilon_span"] == 0.03
    assert c["effective_epsilon_span"] == pytest.approx(0.06)
    # epsilon vs epsilon_mean routed to DISTINCT fields
    c2 = mechanism_definition_contract(_spec("M13", {"operation_axis": "rx", "epsilon": 0.031,
                                                     "epsilon_mean": 0.037}, instruction="rx"))
    assert c2["epsilon"] == 0.031 and c2["epsilon_mean"] == 0.037
    # epsilon absent -> epsilon defaults from epsilon_mean; epsilon_mean absent -> from epsilon
    c3 = mechanism_definition_contract(_spec("M13", {"operation_axis": "rx", "epsilon_mean": 0.041},
                                             instruction="rx"))
    assert c3["epsilon"] == 0.041                       # _m13_epsilon falls back to epsilon_mean
    c4 = mechanism_definition_contract(_spec("M13", {"operation_axis": "rx", "epsilon": 0.043},
                                             instruction="rx"))
    assert c4["epsilon_mean"] == 0.043                  # _m13_epsilon_mean falls back to epsilon
    # both absent -> the 0.03 default (kills the default constants in _m13_epsilon/_mean)
    c5 = mechanism_definition_contract(_spec("M13", {"operation_axis": "rx"}, instruction="rx"))
    assert c5["epsilon"] == 0.03 and c5["epsilon_mean"] == 0.03


def test_L0_definition_contract_M13_drift_weights_normalization_and_reset():
    # _m13_drift_weights teeth (count=3 since default span>0):
    #  * UN-normalized [1,2,1] (sum 4) -> divided by total == [0.25,0.5,0.25] (kills value*total)
    c = mechanism_definition_contract(_spec("M13", {"operation_axis": "rx",
                                                    "drift_mixture_weights": [1.0, 2.0, 1.0]}, instruction="rx"))
    assert c["mixture_weights"] == [0.25, 0.5, 0.25]
    #  * WRONG-length [0.5,0.5] (len 2 != 3, sum > 0) -> reset to default (kills `or`->`and`)
    c2 = mechanism_definition_contract(_spec("M13", {"operation_axis": "rx",
                                                     "drift_mixture_weights": [0.5, 0.5]}, instruction="rx"))
    assert c2["mixture_weights"] == [0.25, 0.5, 0.25]
    #  * ZERO-sum [0,0,0] (len 3, sum 0) -> reset (kills `<=0`->`<0`, whose no-reset path divides by 0)
    c3 = mechanism_definition_contract(_spec("M13", {"operation_axis": "rx",
                                                     "drift_mixture_weights": [0.0, 0.0, 0.0]}, instruction="rx"))
    assert c3["mixture_weights"] == [0.25, 0.5, 0.25]


# =========================================================================== #
# drifted_axis_mixture_kraus -- extra teeth (axis load-bearing in span<=0;      #
# normalization by /total not *total)                                          #
# =========================================================================== #
def test_L0_drifted_axis_mixture_span0_axis_and_unnormalized_weights():
    # span<=0 with a NON-rx axis: _axis_unitary(axis,..) must honor axis (kills axis->None which is rx)
    z = drifted_axis_mixture_kraus("rz", epsilon=0.03, effective_span=0.0)
    _pin(z[0], _rz(0.03), atol=1e-12, label="drift span0 rz")
    # UN-normalized weights [1,2,1] (sum 4 != 1): the module divides by total -> a `*total` mutant diverges
    dv = drifted_axis_mixture_kraus("rx", epsilon=0.02, effective_span=0.08, weights=[1.0, 2.0, 1.0])
    assert_cptp(dv, label="drift unnorm")
    _pin_set(dv, _drift_ref("rx", 0.02, 0.08, [1.0, 2.0, 1.0]), atol=1e-12, label="drift unnorm")


# =========================================================================== #
# thermal_relaxation_kraus -- extra guard-boundary teeth                        #
# =========================================================================== #
def test_L0_thermal_relaxation_guard_boundaries():
    # t1 in (0,1]: kills `t1_>0.0`->`t1_>1.0` (mutant would wrongly raise)
    _pin_set(thermal_relaxation_kraus(0.2, 0.5, 0.5), _thermal(0.2, 0.5, 0.5), atol=1e-11, label="t1<1")
    # t2 in (0,1]: kills `t2_>0.0`->`t2_>1.0`
    _pin_set(thermal_relaxation_kraus(0.2, 0.9, 0.5), _thermal(0.2, 0.9, 0.5), atol=1e-11, label="t2<1")
    # t2 == 0 must raise (kills `t2_>0.0`->`t2_>=0.0`, which would proceed into a 1/0)
    with pytest.raises(ValueError) as e:
        thermal_relaxation_kraus(1.0, 100.0, 0.0)
    assert str(e.value) == "T1, T2 must be positive (T1=100.0, T2=0.0)"
    # t2 just above 2*T1 must raise (kills the `+1e-12`->`+1.0` slack widening)
    with pytest.raises(ValueError) as e2:
        thermal_relaxation_kraus(10.0, 100.0, 200.5)
    assert str(e2.value) == "unphysical T2 > 2 T1 (T2=200.5, T1=100.0)"


# =========================================================================== #
# private-helper direct teeth: _instruction_default_axis + _json_value float    #
# =========================================================================== #
def test_private_instruction_default_axis_get_default():
    # a non-axis instruction falls to the ".get(text, 'rx')" default (kills 'rx'->'RX'/None on THAT get)
    assert ch._instruction_default_axis("measure") == "rx"
    assert ch._instruction_default_axis("ry") == "ry"       # valid alias, not the default
    assert ch._instruction_default_axis(None) == "rx"


def test_private_json_value_floatable_non_basic_uses_float():
    # a floatable NON-basic object reaches `float(value)` (not the isinstance shortcut, not the
    # str() except) -> pins that `float(value)` is `float(value)`, not `float(None)`.
    class _F:
        def __float__(self): return 3.5
        def __repr__(self): return "F"
    assert ch._json_value(_F()) == 3.5 and isinstance(ch._json_value(_F()), float)
    # a non-floatable object hits the except -> str()
    class _O:
        def __repr__(self): return "OBJ"
    assert ch._json_value(_O()) == "OBJ"
