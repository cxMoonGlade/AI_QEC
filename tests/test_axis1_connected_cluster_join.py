"""Step-1 (W-A) regression + GPU certification — connected-cluster joint exponentiation.

Certifies the fix to ``axis1_mcwf_mps_execution._hamiltonian_group_gates``: overlapping-but-
non-identical support Hamiltonian terms must be JOINED into one connected-cluster generator and
exponentiated ONCE (retaining the within-substep cross-term ``[H_i,H_j]``), NOT split into
separate exact-support ``expm`` gates (Lie-Trotter, which drops the commutator — the W-A BLOCKER).

ANTI-CIRCULAR (faithfulness rule I): the reference is the INDEPENDENT oracle
``carrier.joint_lindbladian.assemble_substep_channel`` (sum-all-H → one ``expm(L dt)``,
QuTiP+scipy-validated) AND a from-scratch mixed-radix explicit lift built HERE — NEVER the
carrier's own grouping. The OLD exact-support grouping is reimplemented inline so the RED bracket
(old FAILS, new PASSES) does not depend on the (now-replaced) carrier code.

Standard metric: process (entanglement) infidelity ``1 - F_e = 1 - |Tr(U^dag V)|^2 / D^2`` for the
no-jump Hamiltonian-only unitary channel (phase-invariant); the field-standard channel metric.

GPU-only (memory rule; CPU is not a release basis) — collection FAILS without CUDA.

Run:  conda run -n aiqec python -m pytest -q tests/test_axis1_connected_cluster_join.py
"""
from __future__ import annotations

import itertools

import pytest
import torch

cuda_ok = torch.cuda.is_available()
if not cuda_ok:
    pytest.fail(
        "connected-cluster-join cert is GPU-gated; CUDA-MISSING is NOT A RELEASE BASIS",
        pytrace=False,
    )

from error_coupling_simulator.carrier.joint_lindbladian import (  # noqa: E402
    assemble_substep_channel,
)
from error_coupling_simulator.frontend.axis1_mcwf_mps_execution import (  # noqa: E402
    _hamiltonian_group_gates,
    _hamiltonian_matrix_for_term,
    _lift_hamiltonian_to_cluster,
)

DEVICE = "cuda"
CDT = torch.complex128
TOL_PASS = 1e-9   # (a) exact identity floor (matrix_exp c128)
TOL_RED = 1e-3    # (c) gate: old-grouping defect tripwire


# --------------------------------------------------------------------------- #
# Independent ground-truth embed (NOT the carrier's _lift_hamiltonian_to_cluster).
# Mixed-radix basis walk in the carrier's qubit-0-major convention.
# --------------------------------------------------------------------------- #
def _explicit_lift(H, term_support, cluster_support, local_dims):
    term_support = list(term_support)
    cluster_support = list(cluster_support)
    cdims = [int(local_dims[q]) for q in cluster_support]
    tdims = [int(local_dims[q]) for q in term_support]
    dim = 1
    for d in cdims:
        dim *= d
    out = torch.zeros((dim, dim), dtype=CDT, device=DEVICE)
    Hc = torch.as_tensor(H, dtype=CDT, device=DEVICE)

    def mixed_radix(digits, dims):
        idx = 0
        for d, dim_ in zip(digits, dims):
            idx = idx * dim_ + d
        return idx

    t_pos = [cluster_support.index(q) for q in term_support]
    absent_pos = [i for i, q in enumerate(cluster_support) if q not in term_support]
    for rd in itertools.product(*[range(d) for d in cdims]):
        for cd in itertools.product(*[range(d) for d in cdims]):
            if any(rd[p] != cd[p] for p in absent_pos):
                continue
            rt = mixed_radix([rd[p] for p in t_pos], tdims)
            ct = mixed_radix([cd[p] for p in t_pos], tdims)
            out[mixed_radix(rd, cdims), mixed_radix(cd, cdims)] = Hc[rt, ct]
    return out


def _old_exact_support_group_gates(substep, *, dt_ns, local_dims, device):
    """The OLD exact-support grouping (mirrors the pre-fix carrier; the W-A bug)."""
    groups, order = {}, []
    for term in substep.get("terms", ()):
        if str(term["kind"]) != "hamiltonian":
            continue
        support = tuple(int(q) for q in term["support"])
        H = _hamiltonian_matrix_for_term(term, support=support, local_dims=local_dims, device=device)
        if support not in groups:
            groups[support] = torch.zeros_like(H)
            order.append(support)
        groups[support] = groups[support] + H
    out = []
    for support in order:
        h = 0.5 * (groups[support] + groups[support].conj().transpose(-1, -2))
        out.append({"support": support, "gate": torch.linalg.matrix_exp((-1.0j * float(dt_ns)) * h)})
    return tuple(out)


def _window_unitary_from_gates(gates, *, num_qubits, local_dims):
    full = tuple(range(num_qubits))
    dim = 1
    for q in full:
        dim *= int(local_dims[q])
    U = torch.eye(dim, dtype=CDT, device=DEVICE)
    for g in gates:
        U = _explicit_lift(g["gate"], g["support"], full, local_dims) @ U
    return U


def _joint_window_unitary(terms, *, dt_ns, num_qubits, local_dims):
    full = tuple(range(num_qubits))
    dim = 1
    for q in full:
        dim *= int(local_dims[q])
    H_sum = torch.zeros((dim, dim), dtype=CDT, device=DEVICE)
    for spec in terms:
        support = tuple(int(q) for q in spec["support"])
        H = _hamiltonian_matrix_for_term(spec, support=support, local_dims=local_dims, device=DEVICE)
        H_sum = H_sum + _explicit_lift(H, support, full, local_dims)
    H_sum = 0.5 * (H_sum + H_sum.conj().transpose(-1, -2))
    return torch.linalg.matrix_exp((-1.0j * float(dt_ns)) * H_sum)


def _one_minus_fe(U, V):
    D = U.shape[-1]
    overlap = torch.trace(U.conj().transpose(-1, -2) @ V)
    return float((1.0 - (overlap.abs() ** 2) / (D * D)).real.item())


def _term(family, support, coefficient):
    return {
        "kind": "hamiltonian",
        "operator_family": family,
        "support": list(support),
        "coefficient": float(coefficient),
        "substep_id": "step1_cert",
    }


DIMS = (3, 3, 3)   # qutrit register so the leakage families are representable
DT = 20.0


def _new_gates(substep):
    return _hamiltonian_group_gates(substep, dt_ns=DT, local_dims=DIMS, device=DEVICE)


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #
def test_overlap_old_fails_new_matches_oracle():
    """RED/GREEN: overlapping non-commuting H(0,)+H(0,1). OLD Trotter splits (1-F_e >> 1e-3);
    NEW joins into one cluster gate matching the joint propagator (<= 1e-9)."""
    t1 = _term("LEAK_EXCHANGE_12", (0,), 0.07)
    t2 = _term("LEAK_MOBILITY_12_21", (0, 1), 0.05)
    substep = {"substep_id": "step1_cert", "terms": [t1, t2]}

    joint = _joint_window_unitary([t1, t2], dt_ns=DT, num_qubits=2, local_dims=DIMS)
    old_U = _window_unitary_from_gates(
        _old_exact_support_group_gates(substep, dt_ns=DT, local_dims=DIMS, device=DEVICE),
        num_qubits=2, local_dims=DIMS,
    )
    new = _new_gates(substep)
    new_U = _window_unitary_from_gates(new, num_qubits=2, local_dims=DIMS)

    # non-commuting => the bug is non-vacuous
    H0 = _explicit_lift(_hamiltonian_matrix_for_term(t1, support=(0,), local_dims=DIMS, device=DEVICE), (0,), (0, 1), DIMS)
    H01 = _explicit_lift(_hamiltonian_matrix_for_term(t2, support=(0, 1), local_dims=DIMS, device=DEVICE), (0, 1), (0, 1), DIMS)
    assert float(torch.linalg.matrix_norm(H0 @ H01 - H01 @ H0).item()) > 1e-6

    assert len(new) == 1 and new[0]["support"] == (0, 1)          # fused to one cluster
    assert _one_minus_fe(joint, old_U) > TOL_RED                  # RED: old grouping is broken
    assert _one_minus_fe(joint, new_U) <= TOL_PASS                # GREEN: new matches joint


def test_new_grouping_matches_designated_oracle():
    """The NEW cluster gate matches the DESIGNATED oracle assemble_substep_channel (sum-all-H,
    one expm, Choi->Kraus) — anti-circular, and the joint-window reference matches it too."""
    t1 = _term("LEAK_EXCHANGE_12", (0,), 0.07)
    t2 = _term("LEAK_MOBILITY_12_21", (0, 1), 0.05)
    substep = {"substep_id": "step1_cert", "terms": [t1, t2]}

    H_list = [
        _explicit_lift(_hamiltonian_matrix_for_term(t1, support=(0,), local_dims=DIMS, device=DEVICE), (0,), (0, 1), DIMS),
        _explicit_lift(_hamiltonian_matrix_for_term(t2, support=(0, 1), local_dims=DIMS, device=DEVICE), (0, 1), (0, 1), DIMS),
    ]
    kraus = assemble_substep_channel(H_list, [], DT, device=DEVICE)  # Hamiltonian-only => 1 Kraus
    # dominant Kraus is the unitary (rank-1 Choi for a unitary channel)
    norms = [float(torch.linalg.matrix_norm(K).item()) for K in kraus]
    U_oracle = kraus[int(max(range(len(norms)), key=lambda i: norms[i]))]

    new = _new_gates(substep)
    new_U = _window_unitary_from_gates(new, num_qubits=2, local_dims=DIMS)
    joint = _joint_window_unitary([t1, t2], dt_ns=DT, num_qubits=2, local_dims=DIMS)

    assert _one_minus_fe(U_oracle, joint) <= TOL_PASS      # designated oracle == explicit-lift joint
    assert _one_minus_fe(U_oracle, new_U) <= TOL_PASS      # carrier NEW grouping == designated oracle


def test_disjoint_clusters_stay_factored():
    """Disjoint H(0,)+H(2,) (no shared qubit) stays 2 gates; the factored product is exact."""
    t_a = _term("LEAK_EXCHANGE_12", (0,), 0.06)
    t_b = _term("LEAK_EXCHANGE_12", (2,), 0.04)
    substep = {"substep_id": "step1_cert", "terms": [t_a, t_b]}
    new = _new_gates(substep)
    new_U = _window_unitary_from_gates(new, num_qubits=3, local_dims=DIMS)
    joint = _joint_window_unitary([t_a, t_b], dt_ns=DT, num_qubits=3, local_dims=DIMS)
    assert len(new) == 2                                   # not needlessly fused
    assert _one_minus_fe(joint, new_U) <= TOL_PASS         # commute => factored == joint


def test_chain_closes_transitively():
    """H(0,1)+H(1,2) share qubit 1 => one {0,1,2} cluster (transitive closure); old grouping fails."""
    t_ab = _term("LEAK_MOBILITY_12_21", (0, 1), 0.05)
    t_bc = _term("LEAK_MOBILITY_12_21", (1, 2), 0.045)
    substep = {"substep_id": "step1_cert", "terms": [t_ab, t_bc]}
    joint = _joint_window_unitary([t_ab, t_bc], dt_ns=DT, num_qubits=3, local_dims=DIMS)
    new = _new_gates(substep)
    new_U = _window_unitary_from_gates(new, num_qubits=3, local_dims=DIMS)
    old_U = _window_unitary_from_gates(
        _old_exact_support_group_gates(substep, dt_ns=DT, local_dims=DIMS, device=DEVICE),
        num_qubits=3, local_dims=DIMS,
    )
    assert len(new) == 1 and new[0]["support"] == (0, 1, 2)
    assert _one_minus_fe(joint, old_U) > TOL_RED           # RED
    assert _one_minus_fe(joint, new_U) <= TOL_PASS         # GREEN


def test_same_support_backward_compatible():
    """Co-supported terms are still summed before one expm (the same-support special case)."""
    t_a = _term("ZZ", (0, 1), 0.05)
    t_b = _term("LEAK_MOBILITY_12_21", (0, 1), 0.045)
    substep = {"substep_id": "step1_cert", "terms": [t_a, t_b]}
    new = _new_gates(substep)
    new_U = _window_unitary_from_gates(new, num_qubits=2, local_dims=DIMS)
    joint = _joint_window_unitary([t_a, t_b], dt_ns=DT, num_qubits=2, local_dims=DIMS)
    assert len(new) == 1 and new[0]["support"] == (0, 1)
    assert _one_minus_fe(joint, new_U) <= TOL_PASS


def test_lift_helper_matches_independent_explicit_lift():
    """The carrier's _lift_hamiltonian_to_cluster equals the from-scratch mixed-radix lift
    (exact, all dim/support combos) — the lift algebra itself is certified, not assumed."""
    cases = [
        ((1,), (0, 1), "LEAK_EXCHANGE_12", 0.07),
        ((0,), (0, 1, 2), "LEAK_EXCHANGE_12", 0.05),
        ((0, 2), (0, 1, 2), "LEAK_MOBILITY_12_21", 0.06),  # non-adjacent term support
        ((1, 2), (0, 1, 2), "LEAK_MOBILITY_12_21", 0.04),
    ]
    for term_support, cluster_support, family, coeff in cases:
        H = _hamiltonian_matrix_for_term(
            _term(family, term_support, coeff), support=term_support, local_dims=DIMS, device=DEVICE
        )
        carrier = _lift_hamiltonian_to_cluster(
            H, term_support=term_support, cluster_support=cluster_support, local_dims=DIMS, device=DEVICE
        )
        ref = _explicit_lift(H, term_support, cluster_support, DIMS)
        assert float(torch.linalg.matrix_norm(carrier - ref).item()) <= 1e-12
