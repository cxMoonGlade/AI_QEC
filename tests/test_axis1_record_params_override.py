"""Builder-1 seam tests: per-substep Axis-1 params injection into the dense record emitter.

Covers ``axis1_measurement_record_evidence_manifest(..., params_for_substep=...)``,
``write_axis1_measurement_record_samples(...)``, and ``_enumerate_measurement_records``
(src/qec_twin/simulator/axis1_record_evidence.py) — Path A-corrected per
docs/twin_validation/coupled_cycle_teacher_design.md §2 (reviewer-adjudicated
2026-06-30).

CONSTRAINT LEDGER (faithfulness protocol Rule II — authored BEFORE the implementation;
each constraint names its falsifying test in THIS file):

C1  None-path invariance (a): with ``params_for_substep=None`` (or omitted) the
    evidence payload carries NO new key and is identical to the schedule-global path;
    ``content_hash`` unchanged. Falsified by: ``test_none_path_is_byte_identical``
    (canonical-JSON equality of omitted-kwarg vs explicit-None manifests). The
    untouched repo freeze guards (tests/test_simulator_axis1_schedule.py:6696/:6765)
    stay green on the default path — byte-identity vs the pre-change emitter.
C2  Constant-callable regression (a): a callable returning exactly the schedule-global
    params yields evidence identical to the None path in EVERY field except the
    declared ``params_resolution`` marker. Falsified by:
    ``test_constant_callable_is_regression_identical_modulo_marker``.
C3  Per-substep params reach BOTH generator sides of every selection in the substep
    (a): the H side (static-ZZ zeta -> Hamiltonian edge term) and the c side
    (gamma_phi -> T2 collapse rate) must both carry the callable's per-round values
    inside the ONE joint generator of each selected substep. Falsified by:
    ``test_from_scratch_ground_truth_certifies_injected_per_round_channels`` — an
    implementation that drops either side, applies uniform params, resolves only
    once, or swaps rounds mismatches the independent oracle at >> the 1e-10 gate
    (the in-test dead-callable control shows the discriminating margin > 1e-3), and
    the per-row ``lowered_mechanisms`` coefficient asserts pin zeta (H side) and
    sqrt(2*gamma_phi) (c side) per round exactly.
C4  Enumeration completeness unchanged (a): sum(record_probabilities) = 1 within the
    registered 1e-8 residual and the branch set stays complete under callable
    resolution. Falsified by: residual + record-count asserts in
    ``test_per_round_gamma_phi_variation_changes_records_in_predicted_direction``
    and the ground-truth test.
C5  CPTP of every assembled channel unchanged (a): ``assemble_substep_channel``'s
    loud RuntimeWarning (TP residual > 1e-8) must not fire under per-substep params;
    the ground-truth agreement at 1e-10 bounds any CPTP defect. Falsified by: the
    warnings capture in the ground-truth test.
C6  Resolution happens exactly once per substep that carries selected channels,
    never per selection, in schedule order (a). Falsified by: the invocation-count
    assert (== 8 single-selection gate substeps on the 5q rounds=2 fixture) in
    ``test_constant_callable_is_regression_identical_modulo_marker``; the resolution
    sits structurally OUTSIDE the per-selection loop in the implementation.
C7  Round derivation stays outside the emitter (a, structural): the emitter hands
    the callable the substep object only; ``AnalogSubstepIR.round_index`` is
    compiler-hardcoded None (analog_schedule.py:871/:899) and must never be keyed
    on. Falsified by: ``test_tick_derived_round_mapping_includes_terminal_readout``
    — grounds the tick_index <-> ``round{r}:`` measurement-key mapping
    (record_layout.py:195) INCLUDING the terminal ``final:q{q}:{basis}`` readout
    block (record_layout.py:207; tick_index == rounds; never resolved under the
    default duration policy), and asserts the dead field stays dead.
C8  Fail-loud type contracts (a): a non-callable ``params_for_substep`` and a
    callable returning a non-``Axis1PrimitiveParams`` both raise TypeError naming
    the offense. Falsified by: ``test_fail_loud_type_contracts``.
C9  Isolation unchanged (a, structural): the change adds no learner-payload surface;
    ``params_resolution`` is a mode marker in the evaluator-facing evidence manifest
    (mechanism values were already visible there via ``applied_steps``
    ``lowered_mechanisms`` coefficients). The teacher-side {det,obs}-only projection
    (Builder 2's lane, SPEC §3 constraint 2) is unaffected by this seam.

BOUNDED SIMPLIFICATIONS (Rule III):

S1  Resolution granularity is per-SUBSTEP, not per-selection — EXACT (class a) for
    per-ROUND variation: every selection in a substep shares the substep's tick, and
    the compiler emits one ``tick()`` per round (compiler.py:66-69), so all
    selections in one substep share the round. Zero approximation error for
    round-keyed callables.
S2  The readout/reset instrument stays per-run (slice-1 holds readout/reset at the
    trajectory-mean; SPEC §4, user-resolved 2026-06-30) — a declared class-(c)
    scope recorded in teacher truth (Builder 2's lane), not an approximation
    introduced by this seam.
S3  The callable is resolved only for substeps that carry selected joint channels;
    barrier / reset / no-explicit-duration measurement substeps are never resolved —
    exact w.r.t. the record law (substeps without channels contribute no
    params-dependent evolution). Declared consequence: under the default duration
    policy (analog_schedule.py:464-477 — only gate kinds carry nominal dt) the
    terminal data-readout block (tick_index == rounds) never reaches the callable.
S4  The channel-evidence path (axis1_channel_evidence.py:398,
    ``_channel_row_from_selection`` -> schedule-global params) is NOT extended this
    slice — declared out of scope: the teacher emit seam is the record path;
    extending the channel-evidence manifest would thread four more signatures for no
    slice-1 consumer, failing the brief's "cheap and zero-risk" bar. G2 semantics
    are untouched (zero diff in that file).
S5  Ground-truth tolerance 1e-10 (class c heuristic gate): the instrument floor is
    torch-c128 ``matrix_exp`` scaling-and-squaring + Choi->Kraus identity-sink
    reconstruction (~1e-12..1e-11; cf. the SUPEROP_EXACTZERO_TOL rationale in
    forward/joint_lindbladian.py) + scipy ``expm`` (~1e-13). The in-test
    dead-callable control demonstrates the check discriminates at > 1e-3 — seven
    orders above the gate, so the check is not vacuous.

INDEPENDENT GROUND TRUTH (Rule I): the from-scratch oracle in this file shares NO
code with the emitter: numpy column-stacking Liouvillians (pattern:
tests/test_joint_lindbladian.py:101-115) + ``scipy.linalg.expm`` superoperators +
hand-built Born projectors + hand XOR of the public record-layout wiring. It never
calls the module's superop/Choi/Kraus code and is not a parallel model sharing the
emitter's lowering.

GPU-gated like tests/test_joint_lindbladian.py: collection FAILS without CUDA (a
skip would be a false-green release signal). Run:
  conda run -n aiqec python -m pytest -q tests/test_axis1_record_params_override.py
"""
from __future__ import annotations

import dataclasses
import json
import math
import warnings

import pytest
import torch

if not torch.cuda.is_available():
    pytest.fail(
        "axis1 record params-override tests are GPU-gated; CUDA-MISSING is NOT A RELEASE BASIS",
        pytrace=False,
    )
try:
    import numpy as np
    from scipy.linalg import expm as scipy_expm
except Exception as exc:  # pragma: no cover - environment guard
    pytest.fail(
        "ORACLE-DEPS-MISSING (NOT A RELEASE BASIS): numpy + scipy are required for the "
        f"independent from-scratch record oracle; import error={type(exc).__name__}: {exc}",
        pytrace=False,
    )

from qec_twin.mechanisms.axis1_primitives import Axis1PrimitiveParams  # noqa: E402
from qec_twin.simulator.analog_schedule import (  # noqa: E402
    compile_code_spec_to_substep_schedule,
)
from qec_twin.simulator.axis1_bridge import (  # noqa: E402
    G2_GAMMA_1_PER_NS,
    G2_GAMMA_PHI_PER_NS,
    G2_ZETA_RAD_PER_NS,
)
from qec_twin.simulator.axis1_channel_evidence import (  # noqa: E402
    _axis1_primitive_params_for_schedule,
)
from qec_twin.simulator.axis1_codespec_runner import (  # noqa: E402
    build_axis1_codespec_frontend_spec,
)
from qec_twin.simulator.axis1_record_evidence import (  # noqa: E402
    axis1_measurement_record_evidence_manifest,
    write_axis1_measurement_record_samples,
)
from qec_twin.simulator.code_spec import (  # noqa: E402
    Axis1StaticZZDeviceSpec,
    CodeQubit,
    CodeSpec,
    LogicalObservableSpec,
    PauliTerm,
    StabilizerCheck,
)

ROUNDS = 2
# 5q rounds=2 fixture facts (grounded): 4 single-selection gate substeps per round
# (H(0), CX(0,3), H(0), CX(1,4)) => 8 selected substeps; 7 measurement keys.
FIXTURE_SELECTED_SUBSTEPS = 8


@pytest.fixture(scope="module")
def fixture_schedule():
    return compile_code_spec_to_substep_schedule(
        build_axis1_codespec_frontend_spec(rounds=ROUNDS)
    )


@pytest.fixture(scope="module")
def baseline_manifest(fixture_schedule):
    # kwarg OMITTED: the default-None path (treat as read-only in every test).
    return axis1_measurement_record_evidence_manifest(fixture_schedule)


def _canonical_payload(manifest) -> dict:
    """JSON round-trip so nested dict/list/float compare structurally."""
    return json.loads(json.dumps(manifest, sort_keys=True))


def _record_distribution(manifest) -> dict[tuple[int, ...], float]:
    ev = manifest["record_evidence"]
    out: dict[tuple[int, ...], float] = {}
    for rec, p in zip(
        ev["measurement_records"], ev["record_probabilities"], strict=True
    ):
        key = tuple(int(b) for b in rec)
        out[key] = out.get(key, 0.0) + float(p)
    return out


# --------------------------------------------------------------------------- #
# C1 — identity of the None path                                               #
# --------------------------------------------------------------------------- #
def test_none_path_is_byte_identical(fixture_schedule, baseline_manifest):
    explicit = axis1_measurement_record_evidence_manifest(
        fixture_schedule,
        params_for_substep=None,
    )
    assert "params_resolution" not in explicit
    assert "params_resolution" not in baseline_manifest
    assert explicit["content_hash"] == baseline_manifest["content_hash"]
    assert _canonical_payload(explicit) == _canonical_payload(baseline_manifest)


# --------------------------------------------------------------------------- #
# C2 + C6 — constant callable == None path modulo the declared marker          #
# --------------------------------------------------------------------------- #
def test_constant_callable_is_regression_identical_modulo_marker(
    fixture_schedule, baseline_manifest
):
    global_params = _axis1_primitive_params_for_schedule(fixture_schedule)
    # The fixture carries no lindblad context => the global read IS the G2 defaults
    # (grounds "the SAME params the global read produces" publicly).
    assert global_params == Axis1PrimitiveParams(
        zeta_rad_per_ns=G2_ZETA_RAD_PER_NS,
        gamma_phi_per_ns=G2_GAMMA_PHI_PER_NS,
        gamma_1_per_ns=G2_GAMMA_1_PER_NS,
    )

    calls: list[tuple[str, int]] = []

    def constant_callable(substep):
        calls.append((substep.substep_id, int(substep.tick_index)))
        return global_params

    manifest = axis1_measurement_record_evidence_manifest(
        fixture_schedule,
        params_for_substep=constant_callable,
    )
    assert manifest["params_resolution"] == "per_substep_callable"
    # the marker is INSIDE the hashed payload: callable-mode evidence hashes its mode
    assert manifest["content_hash"] != baseline_manifest["content_hash"]

    left = _canonical_payload(manifest)
    right = _canonical_payload(baseline_manifest)
    assert left.pop("params_resolution") == "per_substep_callable"
    left.pop("content_hash")
    right.pop("content_hash")
    assert left == right

    # C6: exactly once per substep carrying selected channels, never per selection.
    assert len(calls) == FIXTURE_SELECTED_SUBSTEPS
    assert len({sid for sid, _ in calls}) == FIXTURE_SELECTED_SUBSTEPS
    assert {tick for _, tick in calls} == {0, 1}


# --------------------------------------------------------------------------- #
# red-team R1 positive control + physical direction (+ C4)                     #
# --------------------------------------------------------------------------- #
def test_per_round_gamma_phi_variation_changes_records_in_predicted_direction(
    fixture_schedule, baseline_manifest
):
    base = _axis1_primitive_params_for_schedule(fixture_schedule)
    high = dataclasses.replace(base, gamma_phi_per_ns=100.0 * base.gamma_phi_per_ns)
    by_round = {0: base, 1: high}
    # R1 positive control: params MUST differ across rounds for this trajectory.
    assert by_round[0] != by_round[1]

    seen: list[tuple[str, int]] = []

    def per_round(substep):
        tick = int(substep.tick_index)
        assert tick in by_round, f"callable saw unexpected tick_index {tick}"
        seen.append((substep.substep_id, tick))
        return by_round[tick]

    varied = axis1_measurement_record_evidence_manifest(
        fixture_schedule,
        params_for_substep=per_round,
    )

    # (a) invoked with >= 2 distinct tick_index values (per-round resolution is live).
    assert {tick for _, tick in seen} == {0, 1}
    assert len(seen) == FIXTURE_SELECTED_SUBSTEPS

    # (b) the record distribution CHANGES vs the None path (exact enumeration, no
    # shot noise; 100x gamma_phi in round 1 moves probabilities at O(1e-1)).
    base_dist = _record_distribution(baseline_manifest)
    var_dist = _record_distribution(varied)
    assert base_dist.keys() == var_dist.keys()
    max_shift = max(abs(base_dist[k] - var_dist[k]) for k in base_dist)
    assert max_shift > 1.0e-3

    # (c) physically-expected DIRECTION: the x0 check measures X of data qubit 0;
    # after round 0 projects q0 into an X eigenstate, pure dephasing (T2, n-collapse,
    # Z-basis) during round 1 decoheres that eigenstate MONOTONICALLY, so the
    # round-0-vs-round-1 disagreement detector delta:x0:round1 can only gain
    # marginal weight when round-1 gamma_phi rises (class-a direction).
    names = varied["record_evidence"]["detector_names"]
    assert names == baseline_manifest["record_evidence"]["detector_names"]
    idx = names.index("delta:x0:round1")
    m_base = float(baseline_manifest["record_evidence"]["detector_marginals"][idx])
    m_high = float(varied["record_evidence"]["detector_marginals"][idx])
    assert m_high > m_base + 1.0e-3

    # C4: enumeration completeness unchanged under callable resolution.
    ev = varied["record_evidence"]
    assert ev["total_probability_residual"] <= 1.0e-8
    assert ev["record_count"] == baseline_manifest["record_evidence"]["record_count"]


# --------------------------------------------------------------------------- #
# C7 — tick-derived round mapping incl. the terminal data readout              #
# --------------------------------------------------------------------------- #
def test_tick_derived_round_mapping_includes_terminal_readout(fixture_schedule):
    schedule = fixture_schedule
    # the dead field stays dead — a callable must never key on round_index
    # (hardcoded None in both compiler constructors, analog_schedule.py:871/:899).
    assert all(substep.round_index is None for substep in schedule.substeps)

    round_keys: set[str] = set()
    final_keys: set[str] = set()
    for substep in schedule.substeps:
        if substep.kind != "measurement":
            continue
        for key in substep.measurement_keys:
            if key.startswith("round"):
                prefix = key.split(":", 1)[0]
                r = int(prefix[len("round"):])
                assert 0 <= r < ROUNDS
                # tick-derived round == the authoritative round{r}: key label
                assert substep.tick_index == r
                round_keys.add(key)
            else:
                # terminal data readout naming is final:q{qubit}:{basis}
                # (record_layout.py:207-208) and lives at tick_index == rounds.
                assert key.startswith("final:q")
                assert substep.tick_index == ROUNDS
                final_keys.add(key)
    # non-vacuous: the fixture's full key population is present on both sides.
    assert round_keys == {"round0:x0", "round0:z1", "round1:x0", "round1:z1"}
    assert final_keys == {"final:q0:X", "final:q1:Z", "final:q2:Z"}

    # Under the default duration policy only gate substeps carry nominal dt, so the
    # terminal readout block carries NO selected channel: the callable sees exactly
    # ticks {0, .., ROUNDS-1} and is never asked for a "round == ROUNDS" (declared
    # in ledger S3; a future explicit-duration readout window would change this and
    # the callable owner must handle tick_index == rounds explicitly).
    global_params = _axis1_primitive_params_for_schedule(schedule)
    seen_ticks: list[int] = []

    def capture(substep):
        seen_ticks.append(int(substep.tick_index))
        return global_params

    axis1_measurement_record_evidence_manifest(schedule, params_for_substep=capture)
    assert sorted(set(seen_ticks)) == [0, 1]


# --------------------------------------------------------------------------- #
# C8 — fail-loud type contracts                                                #
# --------------------------------------------------------------------------- #
def test_fail_loud_type_contracts(fixture_schedule):
    with pytest.raises(TypeError, match="callable"):
        axis1_measurement_record_evidence_manifest(
            fixture_schedule,
            params_for_substep=42,
        )
    # a bare params object (the subtle misuse) is not a callable either
    with pytest.raises(TypeError, match="callable"):
        axis1_measurement_record_evidence_manifest(
            fixture_schedule,
            params_for_substep=_axis1_primitive_params_for_schedule(fixture_schedule),
        )

    def wrong_return(substep):
        return {"gamma_phi_per_ns": 1.0}

    with pytest.raises(TypeError, match="Axis1PrimitiveParams"):
        axis1_measurement_record_evidence_manifest(
            fixture_schedule,
            params_for_substep=wrong_return,
        )


# --------------------------------------------------------------------------- #
# sampler seam — the kwarg must actually reach the internal manifest call      #
# --------------------------------------------------------------------------- #
def test_sample_writer_threads_callable_through_manifest(fixture_schedule, tmp_path):
    global_params = _axis1_primitive_params_for_schedule(fixture_schedule)
    result = write_axis1_measurement_record_samples(
        fixture_schedule,
        tmp_path / "samples",
        shots=32,
        seed=7,
        params_for_substep=lambda substep: global_params,
    )
    assert result.exact_manifest["params_resolution"] == "per_substep_callable"
    persisted = json.loads(result.exact_evidence.read_text())
    assert persisted["params_resolution"] == "per_substep_callable"
    assert result.detection_events is not None
    assert (
        result.sample_manifest["exact_evidence_content_hash"]
        == result.exact_manifest["content_hash"]
    )


# --------------------------------------------------------------------------- #
# C3/C4/C5 — INDEPENDENT from-scratch ground truth (Rule I)                    #
# --------------------------------------------------------------------------- #
# Smallest sealed multi-round coherence-bearing fixture: 3 qubits, one X check
# (data q0, ancilla q1) + one untouched logical data qubit (q2), rounds=2, ONE
# declared static-ZZ edge (0,1) so the per-round zeta enters the H side of every
# selected generator. Compiled round r (repeated_memory_v1): R(1); H(0); CX(0,1);
# H(0); M(1) key=round{r}:x0; tick. Terminal: M(0) basis X + M(2) basis Z.
# Selected substeps per round (default duration policy, gate kinds only):
#   H(0)  -> one_qubit_drive_zz_cluster_joint_channel, participant (0,1,2), dt=25
#   CX    -> two_qubit_control_zz_cluster_joint_channel, participant (0,1,2), dt=30
#   H(0)  -> one_qubit_drive_zz_cluster_joint_channel, dt=25
# Each generator (grounded lowering conventions):
#   H side: CTRL gate representative + zeta * n(x)n on edge (0,1)
#     CTRL_H  = (pi/(2*25)) * Hd on q0   (SU(2) axis-angle: Hd^2=I, theta=pi/2)
#     CTRL_CX = (pi/(2*30)) * CX(0->1)   (CX^2=I, theta=pi/2; global phase cancels)
#   c side: per qubit q in {0,1,2}: sqrt(2*gamma_phi)*n_q and sqrt(gamma_1)*sm_q
#     (active vs spectator changes the record NAME only, not the operator/rate).

_I2 = np.eye(2, dtype=complex)
_N1 = np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex)
_SM = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=complex)
_PX = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
_HD = (1.0 / np.sqrt(2.0)) * np.array([[1.0, 1.0], [1.0, -1.0]], dtype=complex)
_P0 = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)
_P1 = np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex)

_DT_1Q = 25.0  # h3_h5 policy nominal one_qubit_gate dt (analog_schedule.py:470)
_DT_2Q = 30.0  # h3_h5 policy nominal two_qubit_gate dt (analog_schedule.py:471)


def _kron3(a, b, c):
    return np.kron(np.kron(a, b), c)


def _one_q(op, qubit: int):
    # big-endian qubit order (qubit 0 = leftmost kron factor), matching the
    # emitter's bit convention (idx >> (n-1-q)) & 1 in forward/exact/circuit_sim.
    factors = [_I2, _I2, _I2]
    factors[qubit] = op
    return _kron3(*factors)


_CX01 = _kron3(_P0, _I2, _I2) + _kron3(_P1, _PX, _I2)  # control q0, target q1
_ZZ01 = _kron3(_N1, _N1, _I2)  # declared static edge (0, 1)


def _liouvillian_cs(H, c_list):
    """From-scratch column-stacking Liouvillian (tests/test_joint_lindbladian.py:101
    pattern) — numpy only, shares nothing with the module's builder."""
    D = H.shape[0]
    eye = np.eye(D, dtype=complex)
    L = -1j * (np.kron(eye, H) - np.kron(H.T, eye))
    for c in c_list:
        cc = c.conj().T @ c
        L = L + np.kron(c.conj(), c) - 0.5 * np.kron(eye, cc) - 0.5 * np.kron(cc.T, eye)
    return L


def _apply_superop(S, rho):
    D = rho.shape[0]
    return (S @ rho.reshape(-1, order="F")).reshape(D, D, order="F")


def _collapse_ops(gamma_phi: float, gamma_1: float):
    ops = []
    for q in range(3):
        ops.append(math.sqrt(2.0 * gamma_phi) * _one_q(_N1, q))
        ops.append(math.sqrt(gamma_1) * _one_q(_SM, q))
    return ops


def _round_superops(params: Axis1PrimitiveParams):
    zeta = float(params.zeta_rad_per_ns)
    gphi = float(params.gamma_phi_per_ns)
    g1 = float(params.gamma_1_per_ns)
    H_h = (np.pi / (2.0 * _DT_1Q)) * _one_q(_HD, 0) + zeta * _ZZ01
    H_cx = (np.pi / (2.0 * _DT_2Q)) * _CX01 + zeta * _ZZ01
    S_h = scipy_expm(_liouvillian_cs(H_h, _collapse_ops(gphi, g1)) * _DT_1Q)
    S_cx = scipy_expm(_liouvillian_cs(H_cx, _collapse_ops(gphi, g1)) * _DT_2Q)
    return S_h, S_cx


def _reset_q1(rho):
    # nonselective Z reset to |0>: P0 rho P0 + X P1 rho P1 X
    p0 = _one_q(_P0, 1)
    p1 = _one_q(_P1, 1)
    x1 = _one_q(_PX, 1)
    return p0 @ rho @ p0 + x1 @ (p1 @ rho @ p1) @ x1


def _branch_measure(branches, projectors):
    # unnormalized Born branches: trace(branch) == joint probability of its bits
    out = {}
    for bits, rho in branches.items():
        for m, proj in enumerate(projectors):
            out[bits + (m,)] = proj @ rho @ proj
    return out


def _from_scratch_record_distribution(params_by_round):
    rho0 = np.zeros((8, 8), dtype=complex)
    rho0[0, 0] = 1.0
    branches = {(): rho0}
    pz_q1 = (_one_q(_P0, 1), _one_q(_P1, 1))
    for r in (0, 1):
        S_h, S_cx = _round_superops(params_by_round[r])
        branches = {bits: _reset_q1(m) for bits, m in branches.items()}
        branches = {bits: _apply_superop(S_h, m) for bits, m in branches.items()}
        branches = {bits: _apply_superop(S_cx, m) for bits, m in branches.items()}
        branches = {bits: _apply_superop(S_h, m) for bits, m in branches.items()}
        branches = _branch_measure(branches, pz_q1)
    # terminal readout carries no channel (no explicit readout duration):
    # X on q0 via P^X_m = Hd P_m Hd (== the rotate/Z-project/rotate-back the
    # emitter performs), then Z on q2.
    hd0 = _one_q(_HD, 0)
    px_q0 = (hd0 @ _one_q(_P0, 0) @ hd0, hd0 @ _one_q(_P1, 0) @ hd0)
    branches = _branch_measure(branches, px_q0)
    branches = _branch_measure(branches, (_one_q(_P0, 2), _one_q(_P1, 2)))
    return {bits: float(np.trace(m).real) for bits, m in branches.items()}


def _minimal_coherence_spec() -> CodeSpec:
    metadata = {
        "fixture": "axis1_record_params_override_gt",
        "encoded_distance_certified": False,
    }
    metadata.update(Axis1StaticZZDeviceSpec(edges=((0, 1),), num_qubits=3).to_metadata())
    return CodeSpec(
        name="axis1_minimal_xcheck_gt",
        num_qubits=3,
        data_qubits=(CodeQubit(0, "data", (0.0,)), CodeQubit(2, "data", (2.0,))),
        ancilla_qubits=(CodeQubit(1, "ancilla", (1.0, 0.5)),),
        checks=(StabilizerCheck("x0", 1, (PauliTerm(0, "X"),), (1.0, 0.5)),),
        logical_observables=(
            LogicalObservableSpec("logical_z2", (PauliTerm(2, "Z"),), index=0),
        ),
        rounds=2,
        metadata=metadata,
    )


def test_from_scratch_ground_truth_certifies_injected_per_round_channels():
    spec = _minimal_coherence_spec()
    schedule = compile_code_spec_to_substep_schedule(spec)

    base = Axis1PrimitiveParams(
        zeta_rad_per_ns=0.02,
        gamma_phi_per_ns=G2_GAMMA_PHI_PER_NS,
        gamma_1_per_ns=G2_GAMMA_1_PER_NS,
    )
    high = dataclasses.replace(
        base,
        zeta_rad_per_ns=0.10,
        gamma_phi_per_ns=5.0 * G2_GAMMA_PHI_PER_NS,
    )
    by_round = {0: base, 1: high}

    def per_round(substep):
        tick = int(substep.tick_index)
        assert tick in by_round, f"callable saw unexpected tick_index {tick}"
        return by_round[tick]

    # C5: the assembler's loud non-CPTP warning must not fire under injection.
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        manifest = axis1_measurement_record_evidence_manifest(
            schedule,
            params_for_substep=per_round,
        )
    assert not [
        w for w in caught if "assemble_substep_channel" in str(w.message)
    ], "assembled channel lost CPTP under per-substep params"

    ev = manifest["record_evidence"]
    assert manifest["params_resolution"] == "per_substep_callable"
    assert manifest["passed"] is True
    assert ev["measurement_keys"] == [
        "round0:x0",
        "round1:x0",
        "final:q0:X",
        "final:q2:Z",
    ]
    assert ev["applied_channel_count"] == 6  # 3 gate substeps x 2 rounds
    assert ev["total_probability_residual"] <= 1.0e-8  # C4

    # C3 evidence surface: each applied row's lowered coefficients carry THAT
    # round's zeta (H side) and sqrt(2*gamma_phi) (c side) exactly.
    tick_by_substep = {s.substep_id: int(s.tick_index) for s in schedule.substeps}
    row_kinds = set()
    for row in ev["applied_steps"]:
        expected = by_round[tick_by_substep[row["substep_id"]]]
        row_kinds.add(row["row_kind"])
        by_name = {}
        for rec in row["lowered_mechanisms"]:
            by_name.setdefault(rec["name"], rec)
        assert by_name["ZZ"]["coefficient"] == expected.zeta_rad_per_ns
        assert by_name["T2"]["coefficient"] == math.sqrt(
            2.0 * expected.gamma_phi_per_ns
        )
        assert by_name["T1"]["coefficient"] == math.sqrt(expected.gamma_1_per_ns)
    assert row_kinds == {
        "one_qubit_drive_zz_cluster_joint_channel",
        "two_qubit_control_zz_cluster_joint_channel",
    }

    # C3 channel truth: the emitter's exact record distribution must match the
    # INDEPENDENT from-scratch reconstruction at the declared 1e-10 gate (S5).
    got = _record_distribution(manifest)
    want = _from_scratch_record_distribution(by_round)
    assert abs(sum(want.values()) - 1.0) <= 1.0e-10
    assert set(got) == set(want)
    worst = max(abs(got[k] - want[k]) for k in want)
    assert worst <= 1.0e-10, f"from-scratch GT mismatch: worst |dp| = {worst:.3e}"

    # non-vacuous (Rule II falsifying-test discipline): a DEAD callable (uniform
    # round-0 params, red-team R1) moves the GT distribution >> the gate.
    dead = _from_scratch_record_distribution({0: base, 1: base})
    dead_margin = max(abs(dead[k] - want[k]) for k in want)
    assert dead_margin > 1.0e-3

    # hand-XOR of the public record-layout wiring (class a, structural).
    layout = ev["record_layout_ref"]
    assert [d["name"] for d in layout["detectors"]] == ["delta:x0:round1", "final:x0"]
    assert [o["name"] for o in layout["observables"]] == ["logical_z2"]
    keys = ev["measurement_keys"]

    def _xor_bits(defs, bits):
        return [sum(bits[k] for k in d["keys"]) % 2 for d in defs]

    for rec, det_row, obs_row in zip(
        ev["measurement_records"],
        ev["detector_records"],
        ev["logical_observable_records"],
        strict=True,
    ):
        bits = dict(zip(keys, [int(b) for b in rec], strict=True))
        assert [int(b) for b in det_row] == _xor_bits(layout["detectors"], bits)
        assert [int(b) for b in obs_row] == _xor_bits(layout["observables"], bits)
