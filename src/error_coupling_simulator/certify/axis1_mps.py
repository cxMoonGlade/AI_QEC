from __future__ import annotations

"""Evaluator-side certification for restricted MCWF/MPS execution evidence.

The reference route assembles each substep from its Hamiltonian and collapse
terms with :func:`carrier.joint_lindbladian.assemble_substep_channel`; it does
not reuse the carrier's Hamiltonian grouping. Depending on the available
output, the comparison uses process infidelity, Choi trace distance, record
total variation, or level-population total variation.

The restricted and exact-evidence verdicts use separate project gates because
a one-microstep quantum-jump execution has a declared finite-step error. A
dense-checkable run that exceeds the restricted gate is rejected. A run may be
marked unverified only when its Hilbert-space dimension exceeds the declared
dense-reference cap or it explicitly requires a scalable backend. Sampling
allowances and every threshold are reported with the result; they are software
decision rules rather than physical error bounds.

The dense joint-Lindbladian reference is CUDA-only, so claim-bearing
certification executes on CUDA.
"""

import math
import operator
from numbers import Real
from typing import Any

from ..carrier.mps.controls import (
    normalize_mps_device,
    normalize_mps_index,
    normalize_optional_mps_nonnegative_real,
)
from ..numerics import NUMERICAL_ZERO

# Module-default tolerances. Epistemic class (c): heuristic certification gates /
# tripwires ONLY (go/no-go), never a premise, definition, derivation, or error bound.
#
# Channel path STRICT tau (exact-dense evidence): the carrier's per-substep first-order
# quantum-jump MCWF unraveling (no-jump Kraus I - 1/2 dt c^dag c + jump Kraus sqrt(dt) c) is
# an O(dt^2) Euler approximation to the joint expm(L dt); for a PURE-HAMILTONIAN / closed
# substep the carrier's connected-cluster joint matrix_exp is exact-vs-oracle to the
# matrix_exp floor. So the STRICT gate certifies the exact-dense branch; the GROSS gate
# gates restricted acceptance. Anti-circular: the JOINT oracle is the reference; the carrier
# channel is the object under test.
_PROCESS_INFIDELITY_GATE = 1.0e-6
# CHANNEL GROSS gate tau_gross (restricted-acceptance gate, process infidelity 1-F_e).
# Epistemic class (c): the realized first-order channel finite-step
# error at ``microstep_count=1`` is at most a few times ``1e-2`` in the current
# non-commuting certification fixture, which is
# << a no-op's O(1) channel disagreement (1-F_e ~ 0.42 for an identity-vs-real-dynamics
# channel). tau_gross sits one order ABOVE the worst correct channel finite-step error and
# well BELOW the no-op floor, so a correct m=1 channel run PASSES while a no-op /
# wrong-generator FAILS. A go/no-go tripwire ONLY -- never a premise, derivation, definition,
# or error bound.
_GROSS_GATE = 1.0e-1
# RECORD/LEVEL GROSS gate tau_gross_records (restricted-acceptance gate, TV distance).
# Epistemic class (c) -- justified separately from the channel gate because a single
# first-order MCWF microstep can replace a partial Lindblad decay with a FULL deterministic
# jump, so the worst-correct LEVEL-population TV vs the exact joint-L oracle at m=1 is larger
# than the channel 1-F_e: across the leakage fixtures it is <= ~0.14 (the seepage full-jump
# vs exact partial-decay over dt*gamma=2 gives TV = 1 - e^{-dt*gamma}/... = 0.135), while a
# no-op leaves the population at the initial level (TV = 1) and a wrong-generator splits it
# (TV ~ 0.5). tau_gross_records sits ABOVE the worst correct finite-step systematic (with
# margin) and BELOW the smallest incorrect-run TV. A go/no-go tripwire ONLY.
_GROSS_RECORD_TV_GATE = 0.2
# Hard GROSS-TV ceiling: the gross record/level budget (tau_gross_records + sampling CI) is
# CAPPED at this value so the finite-shot CI at very small trajectory_count (the N=3-5
# deterministic leakage fixtures, where a per-bin Hoeffding half-width can exceed 0.9) cannot
# inflate the budget past the incorrect-run floor. Epistemic class (c) -- justified: it sits
# strictly BELOW the smallest incorrect-run TV (wrong-generator 0.5, no-op 1.0) and ABOVE the
# largest correct TV (~0.14), so no-ops/wrong-branches are ALWAYS rejected regardless of N
# while correct finite-step + legitimately-sampled (N=128) runs pass. A go/no-go tripwire
# ONLY -- never an error bound.
_GROSS_RECORD_TV_CEILING = 0.45
# Record/level STRICT numerical tripwire. Exact probability payloads for MCWF
# level/Record outputs are not registered, so these paths are sampled-only and
# cannot claim exact-dense evidence even when their realized TV is below this
# threshold. The Hoeffding finite-shot CI is surfaced separately.
_RECORD_TV_GATE = 1.0e-6
# Sampled-path finite-shot allowance: a per-bin Hoeffding half-width at this confidence is
# added to the TV gate so a CORRECT sampled carrier is not rejected for shot noise alone,
# while a wrong-branch carrier (TV >> shot noise) is still rejected.
_RECORD_SAMPLING_CONFIDENCE = 0.999
# Normalization invariant gate: a software sanity rule for
# sum(record-frequencies) == 1, not a distinguishability metric.
_NORMALIZATION_INVARIANT_GATE = 1.0e-12
# Window Hilbert dimension above which the dense check is forbidden (true over-cap). A few
# hundred (the brief's "<= a few hundred"); 3^5 = 243 fits, 3^6 = 729 does not. The leakage
# fixtures are 1-2 sites of dim 3-4 (total dim <= 9), all densely checkable.
_DENSE_CHANNEL_MAX_DIM = 256
# Qubit count above which the INDEPENDENT dense Born record oracle
# (axis1_measurement_record_evidence_manifest) is forbidden: it builds an exact 2^N density
# matrix and is itself capped at 8 qubits (axis1_record_evidence._validate_record_evidence_
# schedule). A run above this cap (e.g. the d3 q17 XZZX schedule) is executed
# only as a diagnostic and fails restricted acceptance because no independent
# over-cap Record oracle is registered; it never builds a 2^N density matrix.
_RECORD_EVIDENCE_QUBIT_CAP = 8
_SAMPLED_TRAJECTORY_MODE = "sampled_fixed_microstep_mcwf_trajectories"
_EXACT_BRANCH_MODE = "exact_branch_enumeration"
_ALLOWED_TRAJECTORY_MODES = frozenset(
    {_SAMPLED_TRAJECTORY_MODE, _EXACT_BRANCH_MODE}
)
_RECORD_EVIDENCE_SCHEMA = (
    "error_coupling_simulator.frontend.measurement_record_evidence.v1"
)
_LEVEL_EVIDENCE_SCHEMA = (
    "error_coupling_simulator.carrier.joint_lindbladian."
    "assemble_substep_channel:level_populations"
)
_RECORD_SAMPLING_CI_METHOD = (
    "per_bin_two_sided_hoeffding_capped_at_gross_tv_ceiling"
)
_EVALUATOR_ONLY_DIAGNOSTICS_SCHEMA = (
    "error_coupling_simulator.frontend.mcwf_mps_evaluator_only_diagnostics.v1"
)
_MCWF_METRIC_IDENTITIES = {
    "within_substep_window_channel": (
        "process_infidelity_one_minus_Fe",
        (
            "1 - F_pro; F_pro = Uhlmann fidelity of trace-normalised "
            "Choi states J/D (composed_vs_joint_infidelity convention)"
        ),
        (
            "error_coupling_simulator.carrier.joint_lindbladian."
            "assemble_substep_channel"
        ),
        False,
    ),
    "record_probabilities": (
        "total_variation_distance",
        (
            "TV = 1/2 * sum_i |p_i - q_i| "
            "(Born vs empirical record frequencies)"
        ),
        (
            "error_coupling_simulator.frontend.axis1_record_evidence."
            "axis1_measurement_record_evidence_manifest"
        ),
        False,
    ),
    "level_record_populations": (
        "total_variation_distance",
        (
            "TV = 1/2 * sum_i |p_i - q_i| "
            "(joint-L level populations vs empirical level-record frequencies)"
        ),
        (
            "error_coupling_simulator.carrier.joint_lindbladian."
            "assemble_substep_channel"
        ),
        True,
    ),
}


# --------------------------------------------------------------------------- #
# Piece 1: the MCWF-carrier dense-oracle certification builder.                 #
# --------------------------------------------------------------------------- #
def dense_jointL_record_certification(
    schedule: Any,
    execution: dict[str, Any],
    program: dict[str, Any],
    *,
    declared_local_dims: list[Any] | tuple[Any, ...] | None = None,
    device: str = "cuda",
    process_infidelity_gate: float = _PROCESS_INFIDELITY_GATE,
    record_tv_gate: float = _RECORD_TV_GATE,
    gross_gate: float = _GROSS_GATE,
    record_gross_tv_gate: float = _GROSS_RECORD_TV_GATE,
    record_sampling_confidence: float = _RECORD_SAMPLING_CONFIDENCE,
    dense_channel_max_dim: int = _DENSE_CHANNEL_MAX_DIM,
) -> dict[str, Any]:
    """Certify the MCWF carrier's within-substep output vs the INDEPENDENT joint-L oracle.

    Routing (fail-closed honest ``executed: False`` reasons FIRST), then ONE metric
    comparison vs an oracle independent of the carrier's grouping, returning
    ``{executed, passed, passed_gross, comparison_outcome_is_metric, metric, value, gate,
    gross_gate, ...}``:

      1. over-cap (``requires_scalable_backend``)        -> executed: False (honest).
      2. LEVEL records present (leakage qudit outcomes)  -> ``_certify_level_path``
         (readout-independent level-population reference).
      3. qubit measurement records present               -> ``_certify_record_path``.
      4. no records (Hamiltonian + collapse substep)     -> ``_certify_channel_path``.

    Args:
      schedule  : the ``SubstepSchedule`` (the same object the carrier consumed). Used to
                  build the INDEPENDENT dense oracle.
      execution : the carrier ``mps_execution`` dict (evaluator-only level records under
                  ``evaluator_only_diagnostics``, plus ``record_probabilities``, ``measurement_records``,
                  ``measurement_keys``, ``trajectory_sampling``, ``local_dims``,
                  ``initial_levels`` ...).
      program   : the carrier program manifest (``requires_scalable_backend`` over-cap flag).
      device    : CUDA device for the joint-L reference stack.
      record_gross_tv_gate : explicit registered gross TV base gate. Callers may tighten it;
                             they may not inherit or loosen an ambient/default library cutoff.

    Returns the certification dict consumed by ``restricted_acceptance_policy``.
    """
    device = normalize_mps_device(device)
    dense_channel_max_dim = normalize_mps_index(
        dense_channel_max_dim,
        name="dense_channel_max_dim",
        minimum=1,
    )
    process_infidelity_gate = _normalize_required_nonnegative_real(
        process_infidelity_gate,
        name="process_infidelity_gate",
    )
    record_tv_gate = _normalize_required_nonnegative_real(
        record_tv_gate,
        name="record_tv_gate",
    )
    gross_gate = _normalize_required_nonnegative_real(
        gross_gate,
        name="gross_gate",
    )
    record_gross_tv_gate = _normalize_required_nonnegative_real(
        record_gross_tv_gate,
        name="record_gross_tv_gate",
    )
    if process_infidelity_gate > gross_gate:
        raise ValueError("process_infidelity_gate must not exceed gross_gate")
    if record_tv_gate > min(record_gross_tv_gate, _GROSS_RECORD_TV_CEILING):
        raise ValueError(
            "record_tv_gate must not exceed the effective record gross gate"
        )
    record_sampling_confidence = _normalize_open_unit_interval(
        record_sampling_confidence,
        name="record_sampling_confidence",
    )
    if process_infidelity_gate > _PROCESS_INFIDELITY_GATE:
        raise ValueError("process_infidelity_gate may only tighten the registered default")
    if gross_gate > _GROSS_GATE:
        raise ValueError("gross_gate may only tighten the registered default")
    if record_tv_gate > _RECORD_TV_GATE:
        raise ValueError("record_tv_gate may only tighten the registered default")
    if record_gross_tv_gate > _GROSS_RECORD_TV_GATE:
        raise ValueError(
            "record_gross_tv_gate may only tighten the registered default"
        )
    if record_sampling_confidence > _RECORD_SAMPLING_CONFIDENCE:
        raise ValueError(
            "record_sampling_confidence may not loosen the registered sampling allowance"
        )
    # --- (1) fail-closed honest over-cap reason FIRST. ----------------------------- #
    requires_scalable = _require_exact_bool(
        program["requires_scalable_backend"],
        name="requires_scalable_backend",
    )
    if requires_scalable:
        return {
            "executed": False,
            "passed": False,
            "passed_gross": False,
            "reason": "schedule_contains_scalable_required_rows",
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        }

    sampling = execution.get("trajectory_sampling")
    if not isinstance(sampling, dict):
        raise TypeError("trajectory_sampling must be a mapping")
    sampling_mode = _normalize_trajectory_sampling_mode(sampling["mode"])
    sampled = sampling_mode == _SAMPLED_TRAJECTORY_MODE
    seed_explicit = _require_exact_bool(
        sampling["rng_seed_was_explicit"],
        name="rng_seed_was_explicit",
    )
    trajectory_count = _normalize_positive_index(
        sampling["trajectory_count"],
        name="trajectory_sampling.trajectory_count",
    )

    evaluator_diagnostics = _evaluator_only_diagnostics(execution)
    measurement_keys = _normalize_measurement_keys(
        execution.get("measurement_keys", ())
    )
    _validate_mcwf_measurement_metric_binding(
        execution,
        evaluator_diagnostics=evaluator_diagnostics,
        measurement_keys=measurement_keys,
        declared_local_dims=declared_local_dims,
        program=program,
    )
    has_level_records = bool(evaluator_diagnostics.get("level_records"))
    has_records = bool(measurement_keys)

    # --- (2) level-record path (leakage qudit outcomes). -------------------------- #
    # Routed BEFORE the qubit-record path: leakage schedules carry BOTH measurement_keys
    # and level_records, but the readout-INDEPENDENT level-population comparison is the
    # faithful (and the only oracle-backed) check for a qudit run.
    if has_level_records:
        if not sampled:
            return {
                "executed": False,
                "passed": False,
                "passed_gross": False,
                "reason": "exact_level_probability_payload_not_registered",
                "comparison_outcome_is_metric": False,
                "epistemic_class": "c",
            }
        if sampled and not seed_explicit:
            return {
                "executed": False,
                "passed": False,
                "passed_gross": False,
                "reason": "sampled_level_record_rng_seed_not_explicit",
                "comparison_outcome_is_metric": False,
                "epistemic_class": "c",
            }
        return _certify_level_path(
            schedule,
            execution,
            evaluator_diagnostics=evaluator_diagnostics,
            device=device,
            record_tv_gate=float(record_tv_gate),
            record_sampling_confidence=float(record_sampling_confidence),
            gross_gate=float(record_gross_tv_gate),
            dense_channel_max_dim=dense_channel_max_dim,
            sampled=sampled,
            trajectory_count=trajectory_count,
        )

    # --- (3) qubit measurement-record path. ---------------------------------------- #
    if has_records:
        if not sampled:
            return {
                "executed": False,
                "passed": False,
                "passed_gross": False,
                "reason": "exact_record_probability_payload_not_registered",
                "comparison_outcome_is_metric": False,
                "epistemic_class": "c",
            }
        if sampled and not seed_explicit:
            # A sampled empirical record distribution with no seed is not reproducible
            # evidence -- do NOT certify it (mirrors qt_mps reason for sampled paths).
            return {
                "executed": False,
                "passed": False,
                "passed_gross": False,
                "reason": "sampled_record_rng_seed_not_explicit",
                "comparison_outcome_is_metric": False,
                "epistemic_class": "c",
            }
        return _certify_record_path(
            schedule,
            execution,
            device=device,
            record_tv_gate=float(record_tv_gate),
            record_sampling_confidence=float(record_sampling_confidence),
            gross_gate=float(record_gross_tv_gate),
            sampled=sampled,
            trajectory_count=trajectory_count,
        )

    # --- (4) no measurement records => channel-checkable substep. ------------------ #
    return _certify_channel_path(
        schedule,
        execution,
        device=device,
        process_infidelity_gate=float(process_infidelity_gate),
        gross_gate=float(gross_gate),
        dense_channel_max_dim=dense_channel_max_dim,
    )


# --------------------------------------------------------------------------- #
# LEVEL-record certification path.                                             #
# --------------------------------------------------------------------------- #
def _certify_level_path(
    schedule: Any,
    execution: dict[str, Any],
    *,
    evaluator_diagnostics: dict[str, Any],
    device: str,
    record_tv_gate: float,
    gross_gate: float,
    record_sampling_confidence: float,
    dense_channel_max_dim: int,
    sampled: bool,
    trajectory_count: int,
) -> dict[str, Any]:
    """Readout-INDEPENDENT LEVEL-record cert: carrier level-record frequencies vs the
    INDEPENDENT dense joint-L LEVEL-POPULATION oracle, scored by TV = 1/2 ||p-q||_1
    (+ a Hoeffding finite-shot CI for the sampled MCWF path).

    The oracle (``_dense_jointL_level_distribution``) evolves ``rho0`` (the initial level
    product state) through the program: each dynamics substep advances ``rho`` by the
    DESIGNATED INDEPENDENT ORACLE ``assemble_substep_channel(H_list, c_list, dt)`` on the
    connected window (sum-all -> one ``expm(L dt)`` -- NEVER the carrier's grouping); each
    reset substep applies the projective-reset channel; each measurement substep reads the
    LEVEL-basis DIAGONAL (populations) at its targets and splits ``rho`` into level-
    conditioned branches, accumulating the joint distribution over the recorded level-tuples
    EXACTLY as the carrier records them. Comparing LEVEL POPULATIONS needs no readout model;
    a no-op leaves ``rho0`` => populations stay at the initial level => caught.

    The level-population reference is always built through
    ``_dense_jointL_level_distribution``.
    """
    carrier_level_records = [
        tuple(record)
        for record in _normalize_record_matrix(
            evaluator_diagnostics.get("level_records", ()),
            name="level_records",
            bit_only=False,
        )
    ]
    carrier_counts = _normalize_count_vector(
        evaluator_diagnostics.get("level_record_counts", ()),
        name="level_record_counts",
        require_positive=True,
    )
    if len(carrier_level_records) != len(carrier_counts):
        raise ValueError("level_record_counts length must match level_records")
    if len(set(carrier_level_records)) != len(carrier_level_records):
        raise ValueError("carrier_level_record_distribution contains duplicate outcomes")
    total_counts = int(sum(carrier_counts))
    if sampled and total_counts != trajectory_count:
        raise ValueError(
            "level_record_counts must sum to trajectory_sampling.trajectory_count"
        )
    carrier_dist = {
        rec: float(cnt) / float(total_counts)
        for rec, cnt in zip(carrier_level_records, carrier_counts)
    }
    carrier_dist = _normalize_probability_mapping(
        carrier_dist,
        name="carrier_level_record_distribution",
    )
    if sampled:
        level_probabilities = _normalize_probability_vector(
            evaluator_diagnostics["level_record_probabilities"],
            name="level_record_probabilities",
        )
        if len(level_probabilities) != len(carrier_counts):
            raise ValueError(
                "level_record_probabilities length must match level_record_counts"
            )
        for index, (probability, count) in enumerate(
            zip(level_probabilities, carrier_counts)
        ):
            expected = float(count) / float(trajectory_count)
            if abs(probability - expected) > NUMERICAL_ZERO:
                raise ValueError(
                    "level_record_probabilities"
                    f"[{index}] must equal level_record_counts[{index}] / "
                    "trajectory_sampling.trajectory_count"
                )

    measurement_keys = execution.get("measurement_keys", ())
    if not isinstance(measurement_keys, (list, tuple)):
        raise TypeError("measurement_keys must be a list or tuple")
    _validate_level_record_layout(
        execution,
        level_records=[list(record) for record in carrier_level_records],
        measurement_keys=measurement_keys,
    )

    try:
        oracle_dist = _dense_jointL_level_distribution(
            schedule,
            execution,
            device=device,
            dense_channel_max_dim=int(dense_channel_max_dim),
        )
    except _ChannelNotDenseCheckable as exc:
        return {
            "executed": False,
            "passed": False,
            "passed_gross": False,
            "reason": str(exc),
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        }
    except Exception as exc:  # pragma: no cover - defensive.
        return {
            "executed": False,
            "passed": False,
            "passed_gross": False,
            "reason": "dense_jointL_level_oracle_unavailable",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        }
    oracle_dist = _normalize_probability_mapping(
        oracle_dist,
        name="oracle_level_record_distribution",
    )
    oracle_level_records = _normalize_record_matrix(
        oracle_dist,
        name="oracle_level_records",
        bit_only=False,
    )
    _validate_level_record_layout(
        execution,
        level_records=oracle_level_records,
        measurement_keys=measurement_keys,
        records_name="oracle_level_records",
    )
    oracle_schema = _LEVEL_EVIDENCE_SCHEMA

    tv = _total_variation_distance_dict(carrier_dist, oracle_dist)

    # Finite-shot CI for the sampled carrier path: a per-bin Hoeffding two-sided half-width
    # sqrt( ln(2/alpha) / (2 N) ) at confidence (1 - alpha); TV over K bins inflates by
    # <= (K/2) per-bin width, so the gate budget is tau + sampling_halfwidth. K = the size of
    # the union of the carrier + oracle level supports.
    sampling_halfwidth = 0.0
    if sampled and trajectory_count > 0:
        import math

        n_bins = len(set(carrier_dist) | set(oracle_dist))
        alpha = max(1.0e-12, 1.0 - float(record_sampling_confidence))
        per_bin = math.sqrt(math.log(2.0 / alpha) / (2.0 * float(trajectory_count)))
        sampling_halfwidth = float(0.5 * n_bins * per_bin)

    # The STRICT TV tripwire is not CI-loosened. This level path is sampled-only:
    # passing it remains a numerical diagnostic and cannot create exact-dense
    # evidence. The CI loosens only the gross/restricted tier below.
    strict_effective_gate = float(record_tv_gate)
    gross_effective_gate = _gross_record_tv_budget(
        sampling_halfwidth,
        gross_gate=gross_gate,
    )
    passed_strict = bool(tv <= strict_effective_gate)
    passed_gross = bool(tv <= gross_effective_gate)
    return {
        "executed": True,
        # ``passed`` carries the STRICT decision (exact-dense evidence); ``passed_gross`` the
        # GROSS decision (restricted acceptance). The gate reads ``passed_gross`` for
        # restricted acceptance and ``passed`` for the exact-dense evidence flag.
        "passed": passed_strict,
        "passed_gross": passed_gross,
        "comparison_object": "level_record_populations",
        "oracle": (
            "error_coupling_simulator.carrier.joint_lindbladian."
            "assemble_substep_channel"
        ),
        "oracle_role": "level_basis_diagonal_populations_of_jointL_channel_on_initial_level_state",
        "oracle_independent_of_carrier_grouping": True,
        "readout_model_independent": True,
        "metric": "total_variation_distance",
        "metric_convention": "TV = 1/2 * sum_i |p_i - q_i| (joint-L level populations vs empirical level-record frequencies)",
        "value": float(tv),
        "gate": float(record_tv_gate),
        "gross_gate": float(gross_gate),
        "gross_gate_ceiling": float(_GROSS_RECORD_TV_CEILING),
        "sampling_finite_shot_halfwidth": float(sampling_halfwidth),
        "sampling_support_size": int(n_bins),
        "effective_gate_including_sampling_ci": strict_effective_gate,
        "gross_effective_gate_including_sampling_ci": float(gross_effective_gate),
        "sampling_ci_method": _RECORD_SAMPLING_CI_METHOD,
        "sampling_confidence": float(record_sampling_confidence),
        "trajectory_count": int(trajectory_count),
        "dense_evidence_schema": oracle_schema,
        "comparison_outcome_is_metric": True,
        "metric_epistemic_class": "b",
        "gate_epistemic_class": "c",
        "epistemic_class": "a/c",
    }


def _certify_record_path(
    schedule: Any,
    execution: dict[str, Any],
    *,
    device: str,
    record_tv_gate: float,
    gross_gate: float,
    record_sampling_confidence: float,
    sampled: bool,
    trajectory_count: int,
) -> dict[str, Any]:
    """Qubit measurement-record cert: carrier record_probabilities vs the INDEPENDENT
    dense Born record oracle, scored by TV = 1/2 ||p-q||_1 (+ Hoeffding finite-shot CI).

    The reference is always built by
    ``axis1_measurement_record_evidence_manifest`` and does not reuse the
    carrier's Hamiltonian grouping.
    """
    carrier_records = _normalize_record_matrix(
        execution.get("measurement_records", ()),
        name="carrier_measurement_records",
        bit_only=True,
    )
    carrier_probs = _normalize_probability_vector(
        execution.get("record_probabilities", ()),
        name="carrier_record_probabilities",
    )
    if len(carrier_records) != len(carrier_probs):
        raise ValueError(
            "carrier_record_probabilities length must match measurement_records"
        )
    if sampled:
        carrier_counts = _normalize_count_vector(
            execution["record_counts"],
            name="record_counts",
            require_positive=True,
        )
        if len(carrier_counts) != len(carrier_probs):
            raise ValueError(
                "record_counts length must match carrier_record_probabilities"
            )
        if sum(carrier_counts) != trajectory_count:
            raise ValueError(
                "record_counts must sum to trajectory_sampling.trajectory_count"
            )
        for index, (probability, count) in enumerate(
            zip(carrier_probs, carrier_counts)
        ):
            expected = float(count) / float(trajectory_count)
            if abs(probability - expected) > NUMERICAL_ZERO:
                raise ValueError(
                    "carrier_record_probabilities"
                    f"[{index}] must equal record_counts[{index}] / "
                    "trajectory_sampling.trajectory_count"
                )

    # Honest over-cap routing: the INDEPENDENT dense Born record oracle
    # (axis1_measurement_record_evidence_manifest) builds an exact 2^N density matrix and is
    # capped at AXIS1_RECORD_EVIDENCE_QUBIT_CAP qubits. A genuinely-over-cap run (e.g. the
    # d3 q17 XZZX schedule) must not attempt a 2^N DM build. It returns an
    # unavailable-oracle reason and the acceptance policy fails closed in
    # diagnostic mode. This is checked BEFORE the oracle call so no 2^17 DM is
    # ever constructed.
    # NOTE (belt-and-suspenders): for any measurement-bearing schedule the execution always
    # records level tuples, so certification routes to the LEVEL path FIRST, where the
    # pre-existing _DENSE_CHANNEL_MAX_DIM (256) guard in _dense_jointL_level_distribution is
    # what actually caps q17 (before rho0 is allocated). This record-path guard is the
    # backstop for the (currently unreachable) no-level-records case, not the q17 hot path.
    num_sites = len(execution.get("local_dims", ()))
    if num_sites > _RECORD_EVIDENCE_QUBIT_CAP:
        return {
            "executed": False,
            "passed": False,
            "passed_gross": False,
            "reason": "record_checkable_program_too_large_to_densely_check",
            "num_sites": int(num_sites),
            "record_evidence_qubit_cap": int(_RECORD_EVIDENCE_QUBIT_CAP),
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        }

    try:
        from ..frontend.axis1_record_evidence import (
            axis1_measurement_record_evidence_manifest,
        )

        dense = axis1_measurement_record_evidence_manifest(schedule, device=device)
    except Exception as exc:  # pragma: no cover - defensive (mirrors qt_mps).
        return {
            "executed": False,
            "passed": False,
            "passed_gross": False,
            "reason": "dense_jointL_record_evidence_unavailable",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        }
    dense_record = dense["record_evidence"]
    oracle_records = _normalize_record_matrix(
        dense_record["measurement_records"],
        name="oracle_measurement_records",
        bit_only=True,
    )
    oracle_probs = _normalize_probability_vector(
        dense_record["record_probabilities"],
        name="oracle_record_probabilities",
    )
    if len(oracle_records) != len(oracle_probs):
        raise ValueError(
            "oracle_record_probabilities length must match measurement_records"
        )
    dense_schema = dense.get("schema")
    if dense_schema != _RECORD_EVIDENCE_SCHEMA:
        raise ValueError(
            "dense record evidence schema must match the registered Record oracle"
        )
    dense_hash = _normalize_sha256_text(
        dense.get("content_hash"),
        name="dense record evidence content_hash",
    )

    if oracle_records != carrier_records:
        return {
            "executed": True,
            "passed": False,
            "passed_gross": False,
            "reason": "measurement_record_order_mismatch",
            "metric": "total_variation_distance",
            "comparison_outcome_is_metric": False,
            "dense_evidence_schema": dense_schema,
            "dense_evidence_content_hash": dense_hash,
            "epistemic_class": "c",
        }

    tv = _total_variation_distance(carrier_probs, oracle_probs)

    # Finite-shot CI for the sampled carrier path: a per-bin Hoeffding two-sided half-width
    # sqrt( ln(2/alpha) / (2 N) ) at confidence (1 - alpha); TV over K bins inflates by
    # <= (K/2) per-bin width, so the gate budget is tau_rec + sampling_halfwidth.
    sampling_halfwidth = 0.0
    if sampled and trajectory_count > 0:
        import math

        alpha = max(1.0e-12, 1.0 - float(record_sampling_confidence))
        per_bin = math.sqrt(math.log(2.0 / alpha) / (2.0 * float(trajectory_count)))
        sampling_halfwidth = float(0.5 * len(carrier_probs) * per_bin)

    # The STRICT TV tripwire is not CI-loosened. This Record path is
    # sampled-only: passing it cannot create exact-dense evidence. The CI
    # loosens only the gross/restricted tier below.
    strict_effective_gate = float(record_tv_gate)
    gross_effective_gate = _gross_record_tv_budget(
        sampling_halfwidth,
        gross_gate=gross_gate,
    )
    passed_strict = bool(tv <= strict_effective_gate)
    passed_gross = bool(tv <= gross_effective_gate)
    return {
        "executed": True,
        "passed": passed_strict,
        "passed_gross": passed_gross,
        "comparison_object": "record_probabilities",
        "oracle": (
            "error_coupling_simulator.frontend.axis1_record_evidence."
            "axis1_measurement_record_evidence_manifest"
        ),
        "oracle_independent_of_carrier_grouping": True,
        "metric": "total_variation_distance",
        "metric_convention": "TV = 1/2 * sum_i |p_i - q_i| (Born vs empirical record frequencies)",
        "value": float(tv),
        "gate": float(record_tv_gate),
        "gross_gate": float(gross_gate),
        "gross_gate_ceiling": float(_GROSS_RECORD_TV_CEILING),
        "sampling_finite_shot_halfwidth": float(sampling_halfwidth),
        "sampling_support_size": len(carrier_probs),
        "effective_gate_including_sampling_ci": strict_effective_gate,
        "gross_effective_gate_including_sampling_ci": float(gross_effective_gate),
        "sampling_ci_method": _RECORD_SAMPLING_CI_METHOD,
        "sampling_confidence": float(record_sampling_confidence),
        "trajectory_count": int(trajectory_count),
        "dense_evidence_schema": dense_schema,
        "dense_evidence_content_hash": dense_hash,
        "comparison_outcome_is_metric": True,
        "metric_epistemic_class": "b",
        "gate_epistemic_class": "c",
        "epistemic_class": "a/c",
    }


def _certify_channel_path(
    schedule: Any,
    execution: dict[str, Any],
    *,
    device: str,
    process_infidelity_gate: float,
    gross_gate: float,
    dense_channel_max_dim: int = _DENSE_CHANNEL_MAX_DIM,
) -> dict[str, Any]:
    """Channel-checkable substep cert: carrier realized within-substep window superop vs
    the INDEPENDENT joint-L oracle ``assemble_substep_channel``, scored by process
    infidelity ``1-F_e`` (Choi-state Uhlmann fidelity, the project's
    ``composed_vs_joint_infidelity`` convention) + Choi trace distance.

    ``passed`` = STRICT gate (``1-F_e <= 1e-6``, exact-dense evidence); ``passed_gross`` =
    GROSS gate (``1-F_e <= tau_gross``, restricted acceptance) so a correct ``m=1`` run with
    a real finite-step error passes restricted acceptance while a no-op/wrong-generator
    fails.

    Both channels are built from the current schedule and execution manifest.
    """
    try:
        window = _build_carrier_channel_window(
            schedule, execution, device=device, dense_channel_max_dim=int(dense_channel_max_dim)
        )
    except _ChannelNotDenseCheckable as exc:
        return {
            "executed": False,
            "passed": False,
            "passed_gross": False,
            "reason": str(exc),
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        }
    except Exception as exc:  # pragma: no cover - defensive.
        return {
            "executed": False,
            "passed": False,
            "passed_gross": False,
            "reason": "dense_jointL_channel_oracle_unavailable",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        }
    carrier_superop = window["carrier_superop"]
    oracle_kraus = window["oracle_kraus"]
    oracle_dim = int(window["dim"])

    one_minus_fe, choi_tv = _process_infidelity_and_choi_distance(
        carrier_superop, oracle_kraus, dim=oracle_dim
    )
    one_minus_fe = _normalize_unit_interval_metric(
        one_minus_fe,
        name="process_infidelity",
    )
    choi_tv = _normalize_unit_interval_metric(
        choi_tv,
        name="choi_trace_distance",
    )
    passed_strict = bool(one_minus_fe <= float(process_infidelity_gate))
    passed_gross = bool(one_minus_fe <= float(gross_gate))
    return {
        "executed": True,
        "passed": passed_strict,
        "passed_gross": passed_gross,
        "comparison_object": "within_substep_window_channel",
        "oracle": (
            "error_coupling_simulator.carrier.joint_lindbladian."
            "assemble_substep_channel"
        ),
        "oracle_independent_of_carrier_grouping": True,
        "metric": "process_infidelity_one_minus_Fe",
        "metric_convention": "1 - F_pro; F_pro = Uhlmann fidelity of trace-normalised Choi states J/D (composed_vs_joint_infidelity convention)",
        "value": float(one_minus_fe),
        "gate": float(process_infidelity_gate),
        "gross_gate": float(gross_gate),
        "choi_trace_distance": float(choi_tv),
        "choi_trace_distance_convention": "1/2 * ||J_carrier/D - J_oracle/D||_1 (trace norm of difference of trace-normalised Choi states)",
        "comparison_outcome_is_metric": True,
        "metric_epistemic_class": "b",
        "gate_epistemic_class": "c",
        "epistemic_class": "a/c",
    }


# --------------------------------------------------------------------------- #
# Restricted-acceptance policy (gross/strict split).                            #
# --------------------------------------------------------------------------- #
def restricted_acceptance_policy(
    *,
    execution: dict[str, Any],
    certification: dict[str, Any],
    program: dict[str, Any],
    declared_local_dims: list[Any] | tuple[Any, ...] | None = None,
    rng_seed: int | None,
    trajectory_count: int,
    mass_residual_budget: float | None,
    worst_cut_discarded_weight_gate: float | None = None,
    total_discarded_weight_gate: float | None = None,
) -> dict[str, Any]:
    """Apply the gross/strict dense-reference acceptance policy.

    The policy is
        accepted_for_restricted_execution =
            normalization_invariant_ok
            AND runtime_mass_residual_within_budget
            AND dense_executed AND dense_passed_gross
            AND (seed_explicit if the sampled path is being accepted as evidence)
        accepted_for_exact_dense_probability_evidence =
            accepted AND not sampled AND dense_executed AND dense_passed (STRICT gate).

    A correct ``microstep_count=1`` run (real finite-step error, channel ``1-F_e ~ 1e-2`` /
    sampled-level ``TV`` small) PASSES the GROSS gate => restricted-accepted. A no-op /
    wrong-branch / wrong-generator FAILS the gross gate => rejected. A genuinely-uncheckable
    TRUE-OVERCAP run remains useful diagnostic evidence but cannot pass restricted acceptance.
    A cert that EXECUTED and FAILED the gross gate => REJECT (no fallback).

    Keeps ``total_probability_residual`` but RENAMES its ROLE to ``normalization_invariant``
    (a sum-frequencies sanity invariant, NOT a distinguishability metric). Sets
    ``comparison_outcome_is_metric: True`` ONLY where a real TV / 1-F_e / Choi metric was
    computed.
    """
    if mass_residual_budget is not None:
        if isinstance(mass_residual_budget, bool):
            raise TypeError("mass_residual_budget must be a real threshold, not bool")
        if not isinstance(mass_residual_budget, Real):
            raise TypeError("mass_residual_budget must be a real threshold")
        mass_residual_budget = float(mass_residual_budget)
        if not math.isfinite(mass_residual_budget):
            raise ValueError("mass_residual_budget must be finite")
        if mass_residual_budget < 0.0:
            raise ValueError("mass_residual_budget must be nonnegative")

    normalization_invariant, normalization_invariant_valid = (
        _normalize_finite_nonnegative_real_or_none(
            execution["total_probability_residual"]
        )
    )
    normalization_invariant_ok = bool(
        normalization_invariant_valid
        and normalization_invariant is not None
        and normalization_invariant <= _NORMALIZATION_INVARIANT_GATE
    )
    runtime_mass_residual, runtime_mass_residual_valid = (
        _normalize_finite_nonnegative_real_or_none(
            execution["jump_sampling"]["probability_mass_residual_max"]
        )
    )
    runtime_mass_residual_within_budget = bool(
        mass_residual_budget is not None
        and runtime_mass_residual_valid
        and runtime_mass_residual is not None
        and runtime_mass_residual <= mass_residual_budget
    )
    normalized_rng_seed = _normalize_optional_index(rng_seed, name="rng_seed")
    seed_explicit = normalized_rng_seed is not None

    sampling = execution.get("trajectory_sampling")
    if not isinstance(sampling, dict):
        raise TypeError("trajectory_sampling must be a mapping")
    sampling_mode = _normalize_trajectory_sampling_mode(sampling["mode"])
    sampled = sampling_mode == _SAMPLED_TRAJECTORY_MODE
    normalized_trajectory_count = _normalize_positive_index(
        trajectory_count,
        name="trajectory_count",
    )
    sampling_trajectory_count = _normalize_positive_index(
        sampling["trajectory_count"],
        name="trajectory_sampling.trajectory_count",
    )
    if sampling_trajectory_count != normalized_trajectory_count:
        raise ValueError(
            "trajectory_sampling.trajectory_count must equal trajectory_count"
        )
    requires_scalable = _require_exact_bool(
        program["requires_scalable_backend"],
        name="requires_scalable_backend",
    )

    dense_executed = _require_exact_bool(
        certification["executed"], name="executed"
    )
    dense_passed_strict = _require_exact_bool(
        certification["passed"], name="passed"
    )
    dense_passed_gross = _require_exact_bool(
        certification["passed_gross"], name="passed_gross"
    )
    cert_metric_real = _require_exact_bool(
        certification["comparison_outcome_is_metric"],
        name="comparison_outcome_is_metric",
    )

    if not dense_executed and (dense_passed_strict or dense_passed_gross):
        raise ValueError("non-executed certification cannot report a passing verdict")
    if not cert_metric_real and dense_executed and (
        dense_passed_strict or dense_passed_gross
    ):
        raise ValueError("passing certification must be a metric")
    if cert_metric_real and not dense_executed:
        raise ValueError("metric certification must have executed")

    certification_reason = _normalize_optional_text_field(
        certification,
        "reason",
    )
    if cert_metric_real:
        certification_comparison_object = _require_nonempty_text_field(
            certification,
            "comparison_object",
        )
        certification_metric = _require_nonempty_text_field(
            certification,
            "metric",
        )
        certification_metric_convention = _require_nonempty_text_field(
            certification,
            "metric_convention",
        )
        certification_oracle = _require_nonempty_text_field(
            certification,
            "oracle",
        )
        identity = _MCWF_METRIC_IDENTITIES.get(certification_comparison_object)
        if identity is None:
            raise ValueError(
                "certification.comparison_object is not an allowed MCWF metric identity"
            )
        (
            expected_metric,
            expected_metric_convention,
            expected_oracle,
            requires_readout_independence,
        ) = identity
        if certification_metric != expected_metric:
            raise ValueError(
                "certification.metric does not match certification.comparison_object"
            )
        if certification_metric_convention != expected_metric_convention:
            raise ValueError(
                "certification.metric_convention does not match "
                "certification.comparison_object"
            )
        if certification_oracle != expected_oracle:
            raise ValueError(
                "certification.oracle does not match certification.comparison_object"
            )
        (
            execution_comparison_object,
            execution_support_minimum,
            execution_support_maximum,
        ) = _validate_metric_family_execution_payload(
            execution,
            sampled=sampled,
            trajectory_count=normalized_trajectory_count,
            declared_local_dims=declared_local_dims,
            program=program,
        )
        if certification_comparison_object != execution_comparison_object:
            raise ValueError(
                "certification.comparison_object does not match the execution payload"
            )
        certification_oracle_independent = _require_exact_bool(
            certification["oracle_independent_of_carrier_grouping"],
            name="oracle_independent_of_carrier_grouping",
        )
        if not certification_oracle_independent:
            raise ValueError(
                "certification.oracle_independent_of_carrier_grouping must be true"
            )
        certification_readout_independent = _normalize_optional_bool_field(
            certification,
            "readout_model_independent",
        )
        if requires_readout_independence and certification_readout_independent is not True:
            raise ValueError(
                "certification.readout_model_independent must be true for level records"
            )
        certification_value = _normalize_unit_interval_metric(
            certification["value"],
            name="certification.value",
        )
        certification_gate = _normalize_required_nonnegative_real(
            certification["gate"],
            name="certification.gate",
        )
        certification_gross_gate = _normalize_required_nonnegative_real(
            certification["gross_gate"],
            name="certification.gross_gate",
        )
    else:
        execution_support_minimum = None
        execution_support_maximum = None
        certification_comparison_object = _normalize_optional_text_field(
            certification,
            "comparison_object",
        )
        certification_metric = _normalize_optional_text_field(
            certification,
            "metric",
        )
        certification_metric_convention = _normalize_optional_text_field(
            certification,
            "metric_convention",
        )
        certification_oracle = _normalize_optional_text_field(
            certification,
            "oracle",
        )
        certification_oracle_independent = _normalize_optional_bool_field(
            certification,
            "oracle_independent_of_carrier_grouping",
        )
        certification_readout_independent = _normalize_optional_bool_field(
            certification,
            "readout_model_independent",
        )
        certification_value = _normalize_optional_metric_field(
            certification,
            "value",
        )
        certification_gate = _normalize_optional_metric_field(
            certification,
            "gate",
        )
        certification_gross_gate = _normalize_optional_metric_field(
            certification,
            "gross_gate",
        )
    certification_choi_trace_distance = _normalize_optional_unit_metric_field(
        certification,
        "choi_trace_distance",
    )
    certification_effective_gate = _normalize_optional_metric_field(
        certification,
        "effective_gate_including_sampling_ci",
    )
    certification_gross_effective_gate = _normalize_optional_metric_field(
        certification,
        "gross_effective_gate_including_sampling_ci",
    )
    certification_gross_gate_ceiling = _normalize_optional_metric_field(
        certification,
        "gross_gate_ceiling",
    )
    certification_sampling_halfwidth = _normalize_optional_metric_field(
        certification,
        "sampling_finite_shot_halfwidth",
    )
    certification_sampling_support_size = _normalize_optional_positive_index_field(
        certification,
        "sampling_support_size",
    )
    certification_sampling_method = _normalize_optional_text_field(
        certification,
        "sampling_ci_method",
    )
    certification_sampling_confidence = _normalize_optional_open_unit_field(
        certification,
        "sampling_confidence",
    )
    certification_trajectory_count = _normalize_optional_positive_index_field(
        certification,
        "trajectory_count",
    )
    certification_dense_schema = _normalize_optional_text_field(
        certification,
        "dense_evidence_schema",
    )
    certification_dense_hash = _normalize_optional_sha256_field(
        certification,
        "dense_evidence_content_hash",
    )
    certification_oracle_role = _normalize_optional_text_field(
        certification,
        "oracle_role",
    )
    certification_metric_epistemic_class = _normalize_optional_text_field(
        certification,
        "metric_epistemic_class",
    )
    certification_gate_epistemic_class = _normalize_optional_text_field(
        certification,
        "gate_epistemic_class",
    )
    if cert_metric_real:
        if certification_comparison_object == "within_substep_window_channel":
            if certification_gate > _PROCESS_INFIDELITY_GATE:
                raise ValueError(
                    "channel certification gate may only tighten the registered default"
                )
            if certification_gross_gate > _GROSS_GATE:
                raise ValueError(
                    "channel certification gross gate may only tighten the registered default"
                )
            if any(
                value is not None
                for value in (
                    certification_effective_gate,
                    certification_gross_effective_gate,
                    certification_gross_gate_ceiling,
                    certification_sampling_halfwidth,
                    certification_sampling_support_size,
                    certification_sampling_method,
                    certification_sampling_confidence,
                    certification_trajectory_count,
                    certification_dense_schema,
                    certification_dense_hash,
                )
            ):
                raise ValueError(
                    "channel certification must not carry Record sampling overrides"
                )
            strict_decision_gate = certification_gate
            gross_decision_gate = certification_gross_gate
        else:
            if certification_gate > _RECORD_TV_GATE:
                raise ValueError(
                    "Record certification gate may only tighten the registered default"
                )
            if certification_gross_gate > _GROSS_RECORD_TV_GATE:
                raise ValueError(
                    "Record certification gross gate may only tighten the registered default"
                )
            if certification_effective_gate is None:
                raise ValueError("Record certification requires an effective strict gate")
            if certification_gross_effective_gate is None:
                raise ValueError("Record certification requires an effective gross gate")
            if certification_gross_gate_ceiling is None:
                raise ValueError("Record certification requires a gross gate ceiling")
            if certification_sampling_halfwidth is None:
                raise ValueError("Record certification requires a sampling halfwidth")
            if certification_sampling_support_size is None:
                raise ValueError("Record certification requires a sampling support size")
            if certification_sampling_method != _RECORD_SAMPLING_CI_METHOD:
                raise ValueError("Record certification sampling method is not registered")
            if certification_sampling_confidence is None:
                raise ValueError("Record certification requires sampling confidence")
            if certification_sampling_confidence > _RECORD_SAMPLING_CONFIDENCE:
                raise ValueError(
                    "Record certification sampling confidence may not loosen the "
                    "registered allowance"
                )
            if certification_trajectory_count != normalized_trajectory_count:
                raise ValueError(
                    "certification.trajectory_count must match the execution trajectory count"
                )
            if certification_gross_gate_ceiling != _GROSS_RECORD_TV_CEILING:
                raise ValueError("Record certification gross gate ceiling is not registered")
            if abs(certification_effective_gate - certification_gate) > NUMERICAL_ZERO:
                raise ValueError(
                    "Record certification effective strict gate must equal its base gate"
                )
            if not (
                execution_support_minimum
                <= certification_sampling_support_size
                <= execution_support_maximum
            ):
                raise ValueError(
                    "Record certification sampling support size does not match the execution"
                )
            expected_halfwidth = _sampling_tv_halfwidth(
                sampled=sampled,
                support_size=certification_sampling_support_size,
                trajectory_count=normalized_trajectory_count,
                confidence=certification_sampling_confidence,
            )
            if abs(certification_sampling_halfwidth - expected_halfwidth) > NUMERICAL_ZERO:
                raise ValueError(
                    "Record certification sampling halfwidth does not match its declared inputs"
                )
            expected_gross_effective_gate = _gross_record_tv_budget(
                expected_halfwidth,
                gross_gate=certification_gross_gate,
            )
            if (
                abs(
                    certification_gross_effective_gate
                    - expected_gross_effective_gate
                )
                > NUMERICAL_ZERO
            ):
                raise ValueError(
                    "Record certification effective gross gate does not match its sampling budget"
                )
            if certification_comparison_object == "record_probabilities":
                if certification_dense_schema != _RECORD_EVIDENCE_SCHEMA:
                    raise ValueError("Record certification dense evidence schema is not registered")
                if certification_dense_hash is None:
                    raise ValueError("Record certification requires a dense evidence hash")
            elif certification_dense_schema != _LEVEL_EVIDENCE_SCHEMA:
                raise ValueError("level certification dense evidence schema is not registered")
            strict_decision_gate = certification_effective_gate
            gross_decision_gate = certification_gross_effective_gate
        if gross_decision_gate < strict_decision_gate:
            raise ValueError(
                "certification gross decision gate must not be below strict decision gate"
            )
        expected_passed_strict = certification_value <= strict_decision_gate
        expected_passed_gross = certification_value <= gross_decision_gate
        if dense_passed_strict != expected_passed_strict:
            raise ValueError(
                "certification.passed must equal value <= strict decision gate"
            )
        if dense_passed_gross != expected_passed_gross:
            raise ValueError(
                "certification.passed_gross must equal value <= gross decision gate"
            )
    dense_status = _dense_certification_status(certification)

    # The GROSS positive-evidence path: a real dense-oracle metric comparison passed the
    # GROSS gate. (For a sampled path the cert already folds the rng-seed requirement into
    # its own executed/passed decision, so an unseeded sampled run yields executed=False.)
    dense_evidence_gross = bool(
        dense_executed and dense_passed_gross and cert_metric_real
    )
    # The STRICT exact-dense evidence path: the same comparison passed the STRICT gate.
    dense_evidence_strict = bool(
        dense_executed and dense_passed_strict and cert_metric_real
    )

    # A genuinely uncheckable run may retain diagnostic evidence, but it is not a
    # positive restricted-certification path. A cert that executed and failed its gross gate
    # is likewise rejected rather than routed through an unavailable-oracle fallback.
    overcap_unverified = bool(
        requires_scalable
        or (
            normalization_invariant_ok
            and dense_status == "skipped_overcap_dense_fallback_forbidden"
        )
    )

    # The gate. A sampled path accepted as EMPIRICAL evidence still requires the seed
    # (reproducibility); when accepted via a passed dense metric the seed requirement is
    # already enforced inside the cert.
    sampled_evidence_seed_ok = bool(seed_explicit or not sampled)
    accepted = bool(
        normalization_invariant_ok
        and runtime_mass_residual_within_budget
        and dense_evidence_gross
        and sampled_evidence_seed_ok
        and not requires_scalable
    )

    ledger = execution["mps_truncation_ledger"]
    exact_bond_dimension_sufficient = _normalize_positive_index(
        ledger["exact_bond_dimension_sufficient"],
        name="exact_bond_dimension_sufficient",
    )
    explicit_truncation = _require_exact_bool(
        ledger["explicit_truncation_requested"],
        name="explicit_truncation_requested",
    )
    truncation_ledger_complete = _require_exact_bool(
        ledger["discarded_weight_ledger_complete"],
        name="discarded_weight_ledger_complete",
    )
    accepted_as_exact_bond_representation = _require_exact_bool(
        ledger["accepted_as_exact_bond_representation"],
        name="accepted_as_exact_bond_representation",
    )
    truncation_gate = _mcwf_truncation_gate_result(
        ledger,
        worst_cut_discarded_weight_gate=worst_cut_discarded_weight_gate,
        total_discarded_weight_gate=total_discarded_weight_gate,
    )
    discarded_sum = truncation_gate["observed_total_discarded_weight"]
    worst_cut_discarded_weight = truncation_gate[
        "observed_worst_cut_discarded_weight"
    ]
    truncation_observations_valid = bool(
        discarded_sum is not None and worst_cut_discarded_weight is not None
    )
    truncation_detected = bool(
        discarded_sum is not None and discarded_sum > 0.0
    )
    n_truncating_ops = _require_nonnegative_index_field(
        ledger, "n_truncating_ops"
    )
    if not explicit_truncation:
        if n_truncating_ops != 0 or discarded_sum != 0.0 or worst_cut_discarded_weight != 0.0:
            raise ValueError(
                "unbounded MPS execution cannot report truncation loss"
            )
        if not accepted_as_exact_bond_representation:
            raise ValueError(
                "unbounded MPS execution must be an exact bond representation"
            )
    if (
        n_truncating_ops == 0
        and discarded_sum is not None
        and worst_cut_discarded_weight is not None
        and (discarded_sum != 0.0 or worst_cut_discarded_weight != 0.0)
    ):
        raise ValueError(
            "zero truncating operations cannot carry nonzero truncation loss"
        )
    if (
        worst_cut_discarded_weight is not None
        and worst_cut_discarded_weight > 0.0
        and n_truncating_ops == 0
    ):
        raise ValueError(
            "positive worst-cut loss requires a truncating operation"
        )
    observed_lossless_finite_bond = bool(
        explicit_truncation
        and truncation_ledger_complete
        and truncation_observations_valid
        and n_truncating_ops == 0
    )
    truncation_gate_failed = bool(
        truncation_gate["evaluated"] and not truncation_gate["passed"]
    )
    truncation_gate_complete = bool(
        truncation_gate["worst_cut_discarded_weight_gate"] is not None
        and truncation_gate["total_discarded_weight_gate"] is not None
    )
    finite_bond_candidate = bool(
        explicit_truncation
        and truncation_ledger_complete
        and truncation_gate_complete
        and truncation_gate["evaluated"]
        and truncation_gate["passed"]
    )
    finite_bond_policy_ok = bool(
        not explicit_truncation
        or observed_lossless_finite_bond
        or finite_bond_candidate
    )
    if truncation_gate_failed or not finite_bond_policy_ok:
        accepted = False

    blockers: list[str] = []
    if not normalization_invariant_valid:
        blockers.append("normalization_invariant_invalid")
    elif not normalization_invariant_ok:
        blockers.append("normalization_invariant_exceeds_gate")
    if mass_residual_budget is None:
        blockers.append("mass_residual_budget_not_declared_diagnostic_only")
    elif not runtime_mass_residual_valid:
        blockers.append("runtime_probability_mass_residual_invalid")
    elif not runtime_mass_residual_within_budget:
        blockers.append("runtime_probability_mass_residual_exceeds_budget")
    if not dense_evidence_gross:
        blockers.append(f"dense_jointL_certification:{dense_status}")
    if sampled and not seed_explicit:
        blockers.append("sampled_trajectory_rng_seed_not_explicit")
    if not truncation_ledger_complete:
        blockers.append("incomplete_mps_truncation_aggregation_context")
    if truncation_gate_failed:
        blockers.append("finite_bond_candidate_gate_failed")
    if (
        explicit_truncation
        and not observed_lossless_finite_bond
        and not truncation_gate["evaluated"]
    ):
        blockers.append("finite_bond_candidate_gate_not_evaluated")
    elif (
        explicit_truncation
        and not observed_lossless_finite_bond
        and not truncation_gate_complete
    ):
        blockers.append("finite_bond_candidate_gate_incomplete")
    if truncation_detected:
        blockers.append("nonzero_mps_truncation_discarded_weight")
    if requires_scalable:
        blockers.append("overcap_large_code_policy_not_established")
    blockers.extend(
        [
            "production_error_control_policy_not_established",
            "multilevel_leakage_error_control_not_established",
            "finite_step_error_bound_not_established",
        ]
    )

    if not normalization_invariant_valid:
        certification_status = "rejected"
        diagnostic_only = False
    elif mass_residual_budget is None:
        certification_status = "not_evaluated"
        diagnostic_only = True
    elif (
        not runtime_mass_residual_valid
        or not runtime_mass_residual_within_budget
    ):
        certification_status = "rejected"
        diagnostic_only = False
    elif overcap_unverified or not dense_executed:
        certification_status = "unavailable"
        diagnostic_only = True
    elif accepted:
        certification_status = "accepted"
        diagnostic_only = False
    else:
        certification_status = "rejected"
        diagnostic_only = False

    return {
        "schema": "error_coupling_simulator.frontend.mcwf_mps_restricted_acceptance_policy.v5",
        "policy_role": "restricted_execution_acceptance_not_metric",
        "execution_status": "completed",
        "certification_status": certification_status,
        "diagnostic_only": diagnostic_only,
        "accepted_for_restricted_execution": accepted,
        "accepted_for_sampled_execution_evidence": bool(
            accepted and sampled and dense_evidence_gross
        ),
        # Exact-dense evidence is possible only for a registered un-sampled
        # comparison (currently the no-Record channel path, not level/Record).
        "accepted_for_exact_dense_probability_evidence": bool(
            accepted and not sampled and dense_evidence_strict
        ),
        "accepted_for_production_scalable_backend": False,
        "accepted_as_restricted_overcap_execution": False,
        "blocked_reason": None if accepted else (blockers[0] if blockers else None),
        "gross_strict_gate_split": {
            "gross_gate_role": (
                "restricted_acceptance_gate_catches_gross_disagreement_"
                "no_op_wrong_branch"
            ),
            "strict_gate_role": "exact_dense_probability_evidence_gate",
            "dense_passed_gross": dense_passed_gross if dense_executed else None,
            "dense_passed_strict": dense_passed_strict if dense_executed else None,
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        },
        "dense_jointL_record_certification": {
            "executed": dense_executed,
            "passed": dense_passed_strict if dense_executed else None,
            "passed_gross": dense_passed_gross if dense_executed else None,
            "status": dense_status,
            "comparison_object": certification_comparison_object,
            "metric": certification_metric,
            "metric_convention": certification_metric_convention,
            "value": certification_value,
            "gate": certification_gate,
            "gross_gate": certification_gross_gate,
            "choi_trace_distance": certification_choi_trace_distance,
            "effective_gate_including_sampling_ci": certification_effective_gate,
            "gross_effective_gate_including_sampling_ci": (
                certification_gross_effective_gate
            ),
            "gross_gate_ceiling": certification_gross_gate_ceiling,
            "sampling_finite_shot_halfwidth": certification_sampling_halfwidth,
            "sampling_support_size": certification_sampling_support_size,
            "sampling_ci_method": certification_sampling_method,
            "sampling_confidence": certification_sampling_confidence,
            "trajectory_count": certification_trajectory_count,
            "dense_evidence_schema": certification_dense_schema,
            "dense_evidence_content_hash": certification_dense_hash,
            "oracle": certification_oracle,
            "oracle_role": certification_oracle_role,
            "oracle_independent_of_carrier_grouping": (
                certification_oracle_independent
            ),
            "readout_model_independent": certification_readout_independent,
            # True ONLY where a real TV / 1-F_e / Choi metric was computed.
            "comparison_outcome_is_metric": cert_metric_real,
            "metric_epistemic_class": certification_metric_epistemic_class,
            "gate_epistemic_class": certification_gate_epistemic_class,
            "reason": certification_reason,
        },
        "trajectory": {
            "mode": sampling_mode,
            "trajectory_count": normalized_trajectory_count,
            "rng_seed": normalized_rng_seed,
            "rng_seed_required_for_acceptance": True,
            "rng_seed_was_explicit": seed_explicit,
            "accepted_as_empirical_record_evidence": bool(
                accepted and sampled and dense_evidence_gross
            ),
            "single_trajectory_density_claim": False,
            "comparison_outcome_is_metric": False,
            "epistemic_class": "a/c",
        },
        "finite_step": {
            "exact_summed_lindbladian_claim": False,
            "accepted_as_error_bound": False,
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        },
        "mps_truncation": {
            "explicit_truncation_requested": explicit_truncation,
            "exact_bond_dimension_sufficient": exact_bond_dimension_sufficient,
            "exact_bond_policy": str(ledger["exact_bond_policy"]),
            "accepted_as_exact_bond_representation": (
                accepted_as_exact_bond_representation
            ),
            "discarded_weight_ledger_complete": truncation_ledger_complete,
            "discarded_weight_sum": discarded_sum,
            "worst_cut_discarded_weight": worst_cut_discarded_weight,
            "truncation_detected": truncation_detected,
            "observed_lossless_finite_bond_execution": (
                observed_lossless_finite_bond
            ),
            "gate": truncation_gate,
            "candidate_gate_complete": truncation_gate_complete,
            "accepted_as_finite_bond_candidate": finite_bond_candidate,
            "accepted_as_production_error_bound": False,
            "comparison_outcome_is_metric": False,
            "epistemic_class": str(ledger["epistemic_class"]),
        },
        "probability": {
            # A normalization sanity invariant (sum record frequencies == 1),
            # not a distinguishability metric and never a correctness proxy.
            "normalization_invariant": normalization_invariant,
            "normalization_invariant_is_finite_nonnegative_real": (
                normalization_invariant_valid
            ),
            "normalization_invariant_gate": _NORMALIZATION_INVARIANT_GATE,
            "role": "normalization_sanity_invariant_not_distinguishability_metric",
            "runtime_candidate_mass_residual": runtime_mass_residual,
            "runtime_candidate_mass_residual_budget": mass_residual_budget,
            "runtime_candidate_mass_residual_is_finite_nonnegative": (
                runtime_mass_residual_valid
            ),
            "runtime_candidate_mass_residual_within_budget": (
                None
                if mass_residual_budget is None
                else runtime_mass_residual_within_budget
            ),
            "runtime_candidate_mass_residual_required_for_restricted_acceptance": True,
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        },
        "production_blockers": blockers,
        "scored_quantity_policy": "policy ledger only; the cert metric (1-F_e / Choi / TV) is field-standard, reported not newly defined",
        "comparison_outcome_is_metric": False,
        "epistemic_class": "a/c",
    }


def _dense_certification_status(certification: dict[str, Any]) -> str:
    """Ported from ``axis1_qt_mps_execution._dense_certification_status`` (lines 1432-1444),
    extended for the MCWF reasons. ``passed`` here reflects the STRICT decision; the gate's
    GROSS decision is read separately via ``passed_gross``. A cert that EXECUTED reports
    ``passed``/``failed`` (the STRICT verdict) for transparency, but restricted acceptance is
    decided by ``passed_gross`` upstream -- ``failed`` (strict) does NOT block restricted
    acceptance when ``passed_gross`` is True; what blocks is only a non-executed (overcap /
    unseeded / unavailable) status or an executed-and-gross-failed cert."""
    executed = _require_exact_bool(
        certification["executed"], name="executed"
    )
    if executed:
        # Executed: report the STRICT verdict for the ledger. The gate's restricted-
        # acceptance path keys off ``executed AND passed_gross`` directly (not this string);
        # the exact-dense-evidence path keys off ``executed AND passed`` (strict).
        passed_gross = _require_exact_bool(
            certification["passed_gross"], name="passed_gross"
        )
        passed = _require_exact_bool(
            certification["passed"], name="passed"
        )
        if passed_gross:
            return "passed_gross" if not passed else "passed"
        return "failed"
    reason = _normalize_optional_text_field(certification, "reason")
    if reason is None:
        reason = "not_executed"
    if reason == "schedule_contains_scalable_required_rows":
        return "skipped_overcap_dense_fallback_forbidden"
    if reason in {
        "sampled_record_rng_seed_not_explicit",
        "sampled_level_record_rng_seed_not_explicit",
    }:
        return "skipped_sampled_record_rng_seed_not_explicit"
    if reason in {
        "channel_checkable_substep_too_large_to_densely_check",
        "level_checkable_program_too_large_to_densely_check",
        "record_checkable_program_too_large_to_densely_check",
    }:
        return "skipped_overcap_dense_fallback_forbidden"
    return f"not_executed:{reason}"


def _require_exact_bool(value: Any, *, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{name} must be bool")
    return value


def _mcwf_truncation_gate_result(
    ledger: dict[str, Any],
    *,
    worst_cut_discarded_weight_gate: float | None,
    total_discarded_weight_gate: float | None,
) -> dict[str, Any]:
    """Evaluate MCWF finite-bond policy without importing QT policy code."""

    worst_gate = normalize_optional_mps_nonnegative_real(
        worst_cut_discarded_weight_gate,
        name="worst_cut_discarded_weight_gate",
    )
    total_gate = normalize_optional_mps_nonnegative_real(
        total_discarded_weight_gate,
        name="total_discarded_weight_gate",
    )
    gate_values = {
        "worst_cut_discarded_weight_gate": worst_gate,
        "total_discarded_weight_gate": total_gate,
    }
    ledger_complete = _require_exact_bool(
        ledger["discarded_weight_ledger_complete"],
        name="discarded_weight_ledger_complete",
    )
    worst, worst_is_valid = _normalize_finite_nonnegative_real_or_none(
        ledger["worst_cut_discarded_weight"]
    )
    total, total_is_valid = _normalize_finite_nonnegative_real_or_none(
        ledger["discarded_weight_sum"]
    )
    violations: list[str] = []
    if not ledger_complete:
        violations.append("incomplete_truncation_aggregation_context")
    if not worst_is_valid:
        violations.append("invalid_worst_cut_discarded_weight")
    if not total_is_valid:
        violations.append("invalid_discarded_weight_sum")
    if worst_gate is not None and worst is not None and worst > worst_gate:
        violations.append("worst_cut_discarded_weight_exceeds_gate")
    if total_gate is not None and total is not None and total > total_gate:
        violations.append("total_discarded_weight_exceeds_gate")
    evaluated = bool(
        worst_gate is not None
        or total_gate is not None
        or not ledger_complete
        or not worst_is_valid
        or not total_is_valid
    )
    return {
        "evaluated": evaluated,
        **gate_values,
        "observed_worst_cut_discarded_weight": worst,
        "observed_total_discarded_weight": total,
        "passed": None if not evaluated else not violations,
        "violations": violations,
        "gate_role": "heuristic_finite_bond_policy_gate_not_metric",
        "accepted_as_production_error_bound": False,
        "comparison_outcome_is_metric": False,
        "epistemic_class": "c",
    }


def _dense_reset_basis(name: str) -> str | None:
    """Resolve reset labels independently of either MPS executor."""

    op_name = str(name).upper()
    if op_name in {"R", "RZ"}:
        return "Z"
    if op_name == "RX":
        return "X"
    if op_name == "RY":
        return "Y"
    return None


def _normalize_optional_index(value: Any, *, name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise TypeError(f"{name} must be an integer, not bool")
    try:
        normalized = operator.index(value)
    except TypeError as exc:
        raise TypeError(f"{name} must be an integer") from exc
    return int(normalized)


def _normalize_positive_index(value: Any, *, name: str) -> int:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be an integer, not bool")
    try:
        normalized = operator.index(value)
    except TypeError as exc:
        raise TypeError(f"{name} must be an integer") from exc
    normalized = int(normalized)
    if normalized <= 0:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_index(value: Any, *, name: str) -> int:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be an integer, not bool")
    try:
        normalized = operator.index(value)
    except TypeError as exc:
        raise TypeError(f"{name} must be an integer") from exc
    normalized = int(normalized)
    if normalized < 0:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_trajectory_sampling_mode(value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError("trajectory_sampling.mode must be a string")
    if value not in _ALLOWED_TRAJECTORY_MODES:
        allowed = ", ".join(sorted(_ALLOWED_TRAJECTORY_MODES))
        raise ValueError(
            f"trajectory_sampling.mode must be one of: {allowed}"
        )
    return value


def _normalize_count_vector(
    values: Any,
    *,
    name: str,
    require_positive: bool,
) -> list[int]:
    try:
        raw_values = list(values)
    except TypeError as exc:
        raise TypeError(f"{name} must be an iterable of integers") from exc
    if not raw_values:
        raise ValueError(f"{name} must be nonempty")

    counts: list[int] = []
    for index, value in enumerate(raw_values):
        item_name = f"{name}[{index}]"
        if isinstance(value, bool):
            raise TypeError(f"{item_name} must be an integer, not bool")
        try:
            normalized = operator.index(value)
        except TypeError as exc:
            raise TypeError(f"{item_name} must be an integer") from exc
        normalized = int(normalized)
        if require_positive and normalized <= 0:
            raise ValueError(f"{item_name} must be positive")
        if not require_positive and normalized < 0:
            raise ValueError(f"{item_name} must be nonnegative")
        counts.append(normalized)
    return counts


def _require_nonnegative_index_field(
    mapping: dict[str, Any],
    field: str,
) -> int:
    value = mapping[field]
    if isinstance(value, bool):
        raise TypeError(f"{field} must be a nonnegative integer, not bool")
    try:
        normalized = operator.index(value)
    except TypeError as exc:
        raise TypeError(f"{field} must be a nonnegative integer") from exc
    normalized = int(normalized)
    if normalized < 0:
        raise ValueError(f"{field} must be nonnegative")
    return normalized


def _normalize_finite_nonnegative_real_or_none(
    value: Any,
) -> tuple[float | None, bool]:
    if isinstance(value, bool) or not isinstance(value, Real):
        return None, False
    try:
        normalized = float(value)
    except (TypeError, ValueError, OverflowError):
        return None, False
    if not math.isfinite(normalized) or normalized < 0.0:
        return None, False
    return normalized, True


def _normalize_required_nonnegative_real(value: Any, *, name: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a real threshold, not bool")
    if not isinstance(value, Real):
        raise TypeError(f"{name} must be a real threshold")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{name} must be finite")
    if normalized < 0.0:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_open_unit_interval(value: Any, *, name: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a real probability, not bool")
    if not isinstance(value, Real):
        raise TypeError(f"{name} must be a real probability")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{name} must be finite")
    if not 0.0 < normalized < 1.0:
        raise ValueError(f"{name} must lie strictly between zero and one")
    return normalized


def _normalize_optional_metric_field(
    certification: dict[str, Any],
    field: str,
) -> float | None:
    value = certification.get(field)
    if value is None:
        return None
    return _normalize_required_nonnegative_real(
        value,
        name=f"certification.{field}",
    )


def _normalize_optional_unit_metric_field(
    certification: dict[str, Any],
    field: str,
) -> float | None:
    value = certification.get(field)
    if value is None:
        return None
    return _normalize_unit_interval_metric(
        value,
        name=f"certification.{field}",
    )


def _require_nonempty_text_field(
    values: dict[str, Any],
    field: str,
) -> str:
    value = values[field]
    if not isinstance(value, str) or not value:
        raise TypeError(f"certification.{field} must be a nonempty string")
    return value


def _normalize_optional_text_field(
    values: dict[str, Any],
    field: str,
) -> str | None:
    value = values.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise TypeError(f"certification.{field} must be a nonempty string or null")
    return value


def _normalize_optional_bool_field(
    values: dict[str, Any],
    field: str,
) -> bool | None:
    value = values.get(field)
    if value is None:
        return None
    if type(value) is not bool:
        raise TypeError(f"certification.{field} must be bool or null")
    return value


def _normalize_optional_positive_index_field(
    values: dict[str, Any],
    field: str,
) -> int | None:
    value = values.get(field)
    if value is None:
        return None
    return _normalize_positive_index(value, name=f"certification.{field}")


def _normalize_optional_open_unit_field(
    values: dict[str, Any],
    field: str,
) -> float | None:
    value = values.get(field)
    if value is None:
        return None
    return _normalize_open_unit_interval(value, name=f"certification.{field}")


def _normalize_sha256_text(value: Any, *, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a lowercase SHA-256 hex string")
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 hex string")
    return value


def _normalize_optional_sha256_field(
    values: dict[str, Any],
    field: str,
) -> str | None:
    value = values.get(field)
    if value is None:
        return None
    return _normalize_sha256_text(value, name=f"certification.{field}")


def _normalize_record_matrix(
    values: Any,
    *,
    name: str,
    bit_only: bool,
) -> list[list[int]]:
    try:
        raw_records = list(values)
    except TypeError as exc:
        raise TypeError(f"{name} must be an iterable of records") from exc
    if not raw_records:
        raise ValueError(f"{name} must be nonempty")
    records: list[list[int]] = []
    expected_width: int | None = None
    for record_index, raw_record in enumerate(raw_records):
        try:
            raw_values = list(raw_record)
        except TypeError as exc:
            raise TypeError(f"{name}[{record_index}] must be an iterable") from exc
        if not raw_values:
            raise ValueError(f"{name}[{record_index}] must be nonempty")
        if expected_width is None:
            expected_width = len(raw_values)
        elif len(raw_values) != expected_width:
            raise ValueError(f"{name} records must have equal width")
        record: list[int] = []
        for value_index, value in enumerate(raw_values):
            item_name = f"{name}[{record_index}][{value_index}]"
            if isinstance(value, bool):
                raise TypeError(f"{item_name} must be an integer, not bool")
            try:
                normalized = operator.index(value)
            except TypeError as exc:
                raise TypeError(f"{item_name} must be an integer") from exc
            normalized = int(normalized)
            if bit_only and normalized not in {0, 1}:
                raise ValueError(f"{item_name} must be a bit")
            if not bit_only and normalized < 0:
                raise ValueError(f"{item_name} must be nonnegative")
            record.append(normalized)
        records.append(record)
    if len({tuple(record) for record in records}) != len(records):
        raise ValueError(f"{name} must not contain duplicate outcomes")
    return records


def _normalize_measurement_keys(values: Any) -> list[str]:
    if not isinstance(values, (list, tuple)):
        raise TypeError("measurement_keys must be a list or tuple")
    keys: list[str] = []
    for index, value in enumerate(values):
        if not isinstance(value, str):
            raise TypeError(f"measurement_keys[{index}] must be text")
        if not value:
            raise ValueError(f"measurement_keys[{index}] must be nonempty")
        keys.append(value)
    return keys


def _evaluator_only_diagnostics(execution: dict[str, Any]) -> dict[str, Any]:
    retired_top_level = (
        "level_records",
        "level_record_counts",
        "level_record_probabilities",
    )
    for field in retired_top_level:
        if field in execution:
            raise ValueError(
                f"retired top-level {field} is not accepted; use "
                "evaluator_only_diagnostics"
            )
    jump_sampling = execution.get("jump_sampling")
    if isinstance(jump_sampling, dict) and "jump_family_counts" in jump_sampling:
        raise ValueError(
            "retired jump_sampling.jump_family_counts is not accepted; use "
            "evaluator_only_diagnostics"
        )

    raw = execution.get("evaluator_only_diagnostics")
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise TypeError("evaluator_only_diagnostics must be a mapping")
    if raw.get("schema") != _EVALUATOR_ONLY_DIAGNOSTICS_SCHEMA:
        raise ValueError("evaluator_only_diagnostics schema is not registered")
    if raw.get("visibility") != (
        "evaluator_only_not_emitted_record_or_downstream_estimator_input"
    ):
        raise ValueError("evaluator_only_diagnostics visibility is not registered")
    return raw


def _carrier_program_measurement_layout(
    program: dict[str, Any] | None,
) -> tuple[list[str], list[int], int] | None:
    """Return compiler-sealed measurement layout and site count when available."""

    if program is None:
        return None
    if not isinstance(program, dict):
        raise TypeError("program must be a mapping")
    raw_program = program.get("program")
    if raw_program is None:
        return None
    if not isinstance(raw_program, dict):
        raise TypeError("program.program must be a mapping")
    num_qubits = _normalize_positive_index(
        raw_program.get("num_qubits"),
        name="program.program.num_qubits",
    )
    substeps = raw_program.get("substeps")
    if not isinstance(substeps, (list, tuple)):
        raise TypeError("program.program.substeps must be a list or tuple")

    expected_keys: list[str] = []
    expected_targets: list[int] = []
    for substep_index, substep in enumerate(substeps):
        if not isinstance(substep, dict):
            raise TypeError(
                f"program.program.substeps[{substep_index}] must be a mapping"
            )
        if str(substep.get("substep_kind")) != "measurement":
            continue
        operations = substep.get("operation_records")
        if not isinstance(operations, (list, tuple)):
            raise TypeError(
                "measurement carrier-program operation_records must be a list or tuple"
            )
        for operation_index, operation_record in enumerate(operations):
            if not isinstance(operation_record, dict):
                raise TypeError(
                    "measurement carrier-program operation record must be a mapping"
                )
            keys = _normalize_measurement_keys(
                operation_record.get("measurement_keys", ())
            )
            targets_raw = operation_record.get("targets", ())
            if not isinstance(targets_raw, (list, tuple)):
                raise TypeError(
                    "measurement carrier-program targets must be a list or tuple"
                )
            targets = [
                _normalize_nonnegative_index(
                    value,
                    name=(
                        "program measurement_targets"
                        f"[{substep_index}][{operation_index}][{target_index}]"
                    ),
                )
                for target_index, value in enumerate(targets_raw)
            ]
            if len(keys) != len(targets):
                raise ValueError(
                    "carrier-program measurement keys must match targets"
                )
            for target_index, target in enumerate(targets):
                if target >= num_qubits:
                    raise ValueError(
                        "carrier-program measurement target "
                        f"{target_index} is outside program num_qubits"
                    )
            expected_keys.extend(keys)
            expected_targets.extend(targets)
    return expected_keys, expected_targets, num_qubits


def _validate_mcwf_measurement_metric_binding(
    execution: dict[str, Any],
    *,
    evaluator_diagnostics: dict[str, Any],
    measurement_keys: list[str],
    declared_local_dims: list[Any] | tuple[Any, ...] | None = None,
    program: dict[str, Any] | None = None,
) -> None:
    """Bind measurement layout/dimensions and prevent metric-family downgrade."""

    program_layout = _carrier_program_measurement_layout(program)
    measurement_targets_raw = execution.get("measurement_targets", ())
    if not isinstance(measurement_targets_raw, (list, tuple)):
        raise TypeError("measurement_targets must be a list or tuple")
    measurement_targets = [
        _normalize_nonnegative_index(
            value,
            name=f"measurement_targets[{index}]",
        )
        for index, value in enumerate(measurement_targets_raw)
    ]
    if len(measurement_keys) != len(measurement_targets):
        raise ValueError(
            "measurement_keys length must match measurement_targets"
        )
    program_num_qubits: int | None = None
    if program_layout is not None:
        expected_keys, expected_targets, program_num_qubits = program_layout
        if measurement_keys != expected_keys:
            raise ValueError(
                "execution measurement keys must match carrier program"
            )
        if measurement_targets != expected_targets:
            raise ValueError(
                "execution measurement targets must match carrier program"
            )
    if not measurement_keys:
        return
    local_dims_raw = execution.get("local_dims")
    if not isinstance(local_dims_raw, (list, tuple)) or not local_dims_raw:
        raise ValueError(
            "measured MCWF execution requires declared nonempty local_dims"
        )
    local_dims: list[int] = []
    for index, value in enumerate(local_dims_raw):
        local_dim = _normalize_positive_index(
            value,
            name=f"local_dims[{index}]",
        )
        if local_dim < 2:
            raise ValueError(f"local_dims[{index}] must be at least two")
        local_dims.append(local_dim)
    if not isinstance(declared_local_dims, (list, tuple)) or not declared_local_dims:
        raise ValueError(
            "measured MCWF execution requires independently declared nonempty local_dims"
        )
    normalized_declared_local_dims: list[int] = []
    for index, value in enumerate(declared_local_dims):
        local_dim = _normalize_positive_index(
            value,
            name=f"declared_local_dims[{index}]",
        )
        if local_dim < 2:
            raise ValueError(f"declared_local_dims[{index}] must be at least two")
        normalized_declared_local_dims.append(local_dim)
    if (
        program_num_qubits is not None
        and len(normalized_declared_local_dims) != program_num_qubits
    ):
        raise ValueError(
            "declared_local_dims length must match carrier program num_qubits"
        )
    if local_dims != normalized_declared_local_dims:
        raise ValueError(
            "execution.local_dims must match independently declared_local_dims"
        )
    for index, target in enumerate(measurement_targets):
        if target >= len(local_dims):
            raise ValueError(
                f"measurement_targets[{index}] is outside local_dims"
            )
    if not any(local_dim > 2 for local_dim in local_dims):
        return

    registered_container = execution.get("evaluator_only_diagnostics")
    level_records_raw = evaluator_diagnostics.get("level_records")
    if (
        not isinstance(registered_container, dict)
        or not isinstance(level_records_raw, (list, tuple))
        or not level_records_raw
    ):
        raise ValueError(
            "multilevel measured MCWF execution requires registered "
            "evaluator_only_diagnostics with nonempty level_records"
        )
    level_records = _normalize_record_matrix(
        level_records_raw,
        name="level_records",
        bit_only=False,
    )
    _validate_level_record_layout(
        execution,
        level_records=level_records,
        measurement_keys=measurement_keys,
    )


def _validate_sampled_binary_record_payload(
    execution: dict[str, Any],
    *,
    trajectory_count: int,
) -> int:
    matrix = _normalize_record_matrix(
        execution.get("measurement_records", ()),
        name="measurement_records",
        bit_only=True,
    )
    records = [tuple(row) for row in matrix]
    counts = _normalize_count_vector(
        execution.get("record_counts", ()),
        name="record_counts",
        require_positive=True,
    )
    probabilities = _normalize_probability_vector(
        execution.get("record_probabilities", ()),
        name="record_probabilities",
    )
    if len(records) != len(counts) or len(records) != len(probabilities):
        raise ValueError(
            "sampled measurement records, counts, and probabilities must have "
            "equal lengths"
        )
    if records != sorted(records) or len(set(records)) != len(records):
        raise ValueError(
            "sampled measurement records must be unique and lexicographically "
            "sorted"
        )
    if len(records) > trajectory_count:
        raise ValueError(
            "sampled measurement record support cannot exceed trajectory_count"
        )
    if sum(counts) != trajectory_count:
        raise ValueError("record_counts must sum to trajectory_count")
    for index, (probability, count) in enumerate(
        zip(probabilities, counts, strict=True)
    ):
        expected = float(count) / float(trajectory_count)
        if abs(probability - expected) > NUMERICAL_ZERO:
            raise ValueError(
                f"record_probabilities[{index}] must equal "
                f"record_counts[{index}] / trajectory_count"
            )
    return len(records)


def _validate_metric_family_execution_payload(
    execution: dict[str, Any],
    *,
    sampled: bool,
    trajectory_count: int,
    declared_local_dims: list[Any] | tuple[Any, ...] | None,
    program: dict[str, Any],
) -> tuple[str, int | None, int | None]:
    evaluator_diagnostics = _evaluator_only_diagnostics(execution)
    measurement_keys = _normalize_measurement_keys(
        execution.get("measurement_keys", ())
    )
    _validate_mcwf_measurement_metric_binding(
        execution,
        evaluator_diagnostics=evaluator_diagnostics,
        measurement_keys=measurement_keys,
        declared_local_dims=declared_local_dims,
        program=program,
    )
    if sampled and measurement_keys:
        _validate_sampled_binary_record_payload(
            execution,
            trajectory_count=trajectory_count,
        )
    level_records_raw = evaluator_diagnostics.get("level_records", ())
    if not isinstance(level_records_raw, (list, tuple)):
        raise TypeError("level_records must be a list or tuple")

    if level_records_raw:
        if not sampled:
            raise ValueError(
                "exact level-record probability payload is not registered for MCWF"
            )
        level_records = _normalize_record_matrix(
            level_records_raw,
            name="level_records",
            bit_only=False,
        )
        level_counts = _normalize_count_vector(
            evaluator_diagnostics.get("level_record_counts", ()),
            name="level_record_counts",
            require_positive=True,
        )
        if len(level_records) != len(level_counts):
            raise ValueError("level_record_counts length must match level_records")
        if sampled:
            if sum(level_counts) != trajectory_count:
                raise ValueError(
                    "level_record_counts must sum to trajectory_count"
                )
            probabilities = _normalize_probability_vector(
                evaluator_diagnostics.get("level_record_probabilities", ()),
                name="level_record_probabilities",
            )
            if len(probabilities) != len(level_counts):
                raise ValueError(
                    "level_record_probabilities length must match level_record_counts"
                )
            for index, (probability, count) in enumerate(
                zip(probabilities, level_counts)
            ):
                expected = float(count) / float(trajectory_count)
                if abs(probability - expected) > NUMERICAL_ZERO:
                    raise ValueError(
                        "level_record_probabilities"
                        f"[{index}] must equal level_record_counts[{index}] / trajectory_count"
                    )
        support_upper_bound = _validate_level_record_layout(
            execution,
            level_records=level_records,
            measurement_keys=measurement_keys,
        )
        return (
            "level_record_populations",
            len(level_records),
            support_upper_bound,
        )

    if measurement_keys:
        if not sampled:
            raise ValueError(
                "exact measurement-record probability payload is not registered for MCWF"
            )
        records = _normalize_record_matrix(
            execution.get("measurement_records", ()),
            name="measurement_records",
            bit_only=True,
        )
        probabilities = _normalize_probability_vector(
            execution.get("record_probabilities", ()),
            name="record_probabilities",
        )
        if len(records) != len(probabilities):
            raise ValueError(
                "record_probabilities length must match measurement_records"
            )
        if sampled:
            counts = _normalize_count_vector(
                execution.get("record_counts", ()),
                name="record_counts",
                require_positive=True,
            )
            if len(counts) != len(probabilities):
                raise ValueError("record_counts length must match record_probabilities")
            if sum(counts) != trajectory_count:
                raise ValueError("record_counts must sum to trajectory_count")
            for index, (probability, count) in enumerate(zip(probabilities, counts)):
                expected = float(count) / float(trajectory_count)
                if abs(probability - expected) > NUMERICAL_ZERO:
                    raise ValueError(
                        "record_probabilities"
                        f"[{index}] must equal record_counts[{index}] / trajectory_count"
                    )
        return "record_probabilities", len(records), len(records)

    measurement_targets = execution.get("measurement_targets", ())
    if not isinstance(measurement_targets, (list, tuple)):
        raise TypeError("measurement_targets must be a list or tuple")
    if measurement_targets:
        raise ValueError("no-measurement channel payload cannot carry measurement_targets")
    for field in ("level_record_counts", "level_record_probabilities"):
        residue = evaluator_diagnostics.get(field, ())
        if not isinstance(residue, (list, tuple)):
            raise TypeError(
                f"no-measurement channel payload {field} must be a list or tuple"
            )
        if residue:
            raise ValueError(
                "no-measurement channel payload cannot carry level-record residue"
            )

    measurement_records = execution.get("measurement_records")
    if not (
        isinstance(measurement_records, (list, tuple))
        and len(measurement_records) == 1
        and isinstance(measurement_records[0], (list, tuple))
        and len(measurement_records[0]) == 0
    ):
        raise ValueError(
            "no-measurement channel payload requires measurement_records=[[]]"
        )
    record_counts = _normalize_count_vector(
        execution.get("record_counts", ()),
        name="record_counts",
        require_positive=True,
    )
    if record_counts != [trajectory_count]:
        raise ValueError(
            "no-measurement channel payload requires record_counts=[trajectory_count]"
        )
    record_probabilities = _normalize_probability_vector(
        execution.get("record_probabilities", ()),
        name="record_probabilities",
    )
    if record_probabilities != [1.0]:
        raise ValueError(
            "no-measurement channel payload requires record_probabilities=[1.0]"
        )
    return "within_substep_window_channel", None, None


def _validate_level_record_layout(
    execution: dict[str, Any],
    *,
    level_records: list[list[int]],
    measurement_keys: list[Any] | tuple[Any, ...],
    records_name: str = "level_records",
) -> int:
    local_dims_raw = execution.get("local_dims")
    if not isinstance(local_dims_raw, (list, tuple)) or not local_dims_raw:
        raise ValueError("level-record execution requires local_dims")
    local_dims: list[int] = []
    for index, value in enumerate(local_dims_raw):
        local_dim = _normalize_positive_index(
            value,
            name=f"local_dims[{index}]",
        )
        if local_dim < 2:
            raise ValueError(f"local_dims[{index}] must be at least two")
        local_dims.append(local_dim)

    measurement_targets_raw = execution.get("measurement_targets")
    if not isinstance(measurement_targets_raw, (list, tuple)):
        raise TypeError("measurement_targets must be a list or tuple")
    if not measurement_targets_raw:
        raise ValueError("level-record execution requires measurement_targets")
    measurement_targets: list[int] = []
    for index, value in enumerate(measurement_targets_raw):
        target = _normalize_nonnegative_index(
            value,
            name=f"measurement_targets[{index}]",
        )
        if target >= len(local_dims):
            raise ValueError(
                f"measurement_targets[{index}] is outside local_dims"
            )
        measurement_targets.append(target)

    if len(measurement_keys) != len(measurement_targets):
        raise ValueError(
            "measurement_keys length must match measurement_targets"
        )
    for record_index, record in enumerate(level_records):
        if len(record) != len(measurement_targets):
            raise ValueError(
                f"{records_name}[{record_index}] width must match measurement_targets"
            )
        for value_index, (level, target) in enumerate(
            zip(record, measurement_targets, strict=True)
        ):
            if level >= local_dims[target]:
                raise ValueError(
                    f"{records_name}[{record_index}][{value_index}] is outside "
                    f"local_dims[{target}]"
                )

    return math.prod(local_dims[target] for target in measurement_targets)


def _sampling_tv_halfwidth(
    *,
    sampled: bool,
    support_size: int,
    trajectory_count: int,
    confidence: float,
) -> float:
    if not sampled:
        return 0.0
    alpha = max(1.0e-12, 1.0 - float(confidence))
    per_bin = math.sqrt(math.log(2.0 / alpha) / (2.0 * float(trajectory_count)))
    return float(0.5 * int(support_size) * per_bin)


def _normalize_probability_vector(values: Any, *, name: str) -> list[float]:
    try:
        raw_values = list(values)
    except TypeError as exc:
        raise TypeError(f"{name} must be an iterable of real probabilities") from exc
    if not raw_values:
        raise ValueError(f"{name} must be nonempty")

    probabilities: list[float] = []
    for index, value in enumerate(raw_values):
        item_name = f"{name}[{index}]"
        if isinstance(value, bool):
            raise TypeError(f"{item_name} must be a real probability, not bool")
        if not isinstance(value, Real):
            raise TypeError(f"{item_name} must be a real probability")
        normalized = float(value)
        if not math.isfinite(normalized):
            raise ValueError(f"{item_name} must be finite")
        if normalized < 0.0:
            raise ValueError(f"{item_name} must be nonnegative")
        probabilities.append(normalized)

    total = math.fsum(probabilities)
    if abs(total - 1.0) > NUMERICAL_ZERO:
        raise ValueError(
            f"{name} must sum to one within NUMERICAL_ZERO={NUMERICAL_ZERO}"
        )
    return probabilities


def _normalize_probability_mapping(
    values: Any,
    *,
    name: str,
) -> dict[Any, float]:
    if not isinstance(values, dict):
        raise TypeError(f"{name} must be a mapping")
    if not values:
        raise ValueError(f"{name} must be nonempty")

    probabilities: dict[Any, float] = {}
    for outcome, value in values.items():
        item_name = f"{name}[{outcome!r}]"
        if isinstance(value, bool):
            raise TypeError(f"{item_name} must be a real probability, not bool")
        if not isinstance(value, Real):
            raise TypeError(f"{item_name} must be a real probability")
        normalized = float(value)
        if not math.isfinite(normalized):
            raise ValueError(f"{item_name} must be finite")
        if normalized < 0.0:
            raise ValueError(f"{item_name} must be nonnegative")
        probabilities[outcome] = normalized

    total = math.fsum(probabilities.values())
    if abs(total - 1.0) > NUMERICAL_ZERO:
        raise ValueError(
            f"{name} must sum to one within NUMERICAL_ZERO={NUMERICAL_ZERO}"
        )
    return probabilities


def _normalize_unit_interval_metric(value: Any, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real metric value")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{name} must be finite")
    if normalized < -NUMERICAL_ZERO or normalized > 1.0 + NUMERICAL_ZERO:
        raise ValueError(f"{name} must lie in [0, 1]")
    return min(1.0, max(0.0, normalized))


# --------------------------------------------------------------------------- #
# Metric helpers (field-standard; conventions carried).                         #
# --------------------------------------------------------------------------- #
def _gross_record_tv_budget(
    sampling_halfwidth: float,
    *,
    gross_gate: float,
) -> float:
    """Return ``min(explicit_gross_gate + sampling_halfwidth, gross_ceiling)``.

    The Hoeffding ``sampling_halfwidth`` prevents legitimate sampled runs (for example,
    ``N=128``) from failing solely due to shot noise. The fixed ceiling prevents a tiny-N
    interval from inflating the allowance past the incorrect-run TV floor (wrong generator
    0.5, no-op 1.0). The base gate is an explicit policy input, not an inherited numerical
    library default. Epistemic class (c).
    """
    return float(
        min(float(gross_gate) + float(sampling_halfwidth), _GROSS_RECORD_TV_CEILING)
    )


def _total_variation_distance(p, q) -> float:
    """TV = 1/2 ||p-q||_1 over a shared support ordering (the standard statistical-distance
    convention; in [0,1])."""
    if len(p) != len(q):
        raise ValueError("TV distance requires equal-length probability vectors")
    value = float(0.5 * sum(abs(float(a) - float(b)) for a, b in zip(p, q)))
    return _normalize_unit_interval_metric(value, name="total_variation_distance")


def _total_variation_distance_dict(p: dict, q: dict) -> float:
    """TV = 1/2 sum_k |p_k - q_k| between two distributions keyed by outcome (the union of
    supports; missing keys contribute 0). The standard statistical-distance convention; in
    [0,1] for two probability distributions."""
    keys = set(p) | set(q)
    value = float(
        0.5
        * sum(abs(float(p.get(k, 0.0)) - float(q.get(k, 0.0))) for k in keys)
    )
    return _normalize_unit_interval_metric(value, name="total_variation_distance")


def _process_infidelity_and_choi_distance(carrier_superop, oracle_kraus, *, dim: int):
    """Process infidelity ``1 - F_e`` (Choi-state Uhlmann fidelity) + Choi trace distance
    between the carrier window superoperator and the reference Kraus channel.

    numpy implementation that REPRODUCES the project's GPU convention EXACTLY
    (``joint_lindbladian._choi_state_from_kraus`` / ``_state_fidelity`` /
    ``composed_vs_joint_infidelity``, lines 494-573): column-stacking superop -> channel
    action; trace-normalised Choi states ``J/D``; Uhlmann fidelity via eigendecomposition;
    return ``max(0, 1 - F_pro)`` and ``1/2 ||J_c - J_o||_1`` (trace norm = sum|eigvals| of a
    Hermitian difference). The calculation is performed in NumPy after channel
    construction.
    """
    import numpy as np

    D = int(dim)
    carrier_superop = np.asarray(carrier_superop, dtype=np.complex128)
    if carrier_superop.shape != (D * D, D * D):
        raise ValueError(
            f"carrier superop shape {carrier_superop.shape} != ({D * D}, {D * D})"
        )

    def _channel_action_superop(S, rho):
        # column-stacking: vec(rho) stacks COLUMNS (Fortran order); E(rho) = unvec(S @ vec(rho)).
        v = np.asarray(rho, dtype=np.complex128).reshape(D * D, order="F")
        out = S @ v
        return out.reshape(D, D, order="F")

    def _channel_action_kraus(kraus, rho):
        acc = np.zeros((D, D), dtype=np.complex128)
        for K in kraus:
            K = np.asarray(K, dtype=np.complex128)
            acc = acc + K @ rho @ K.conj().T
        return acc

    def _choi_state(apply_fn):
        J = np.zeros((D * D, D * D), dtype=np.complex128)
        for p in range(D):
            for qd in range(D):
                rho = np.zeros((D, D), dtype=np.complex128)
                rho[p, qd] = 1.0
                Epq = apply_fn(rho)
                epq = np.zeros((D, D), dtype=np.complex128)
                epq[p, qd] = 1.0
                J = J + np.kron(Epq, epq)
        J = 0.5 * (J + J.conj().T)
        tr = np.trace(J).real
        return J / tr

    J_carrier = _choi_state(lambda rho: _channel_action_superop(carrier_superop, rho))
    J_oracle = _choi_state(lambda rho: _channel_action_kraus(oracle_kraus, rho))

    # Uhlmann fidelity of the two trace-normalised Choi states.
    F_pro = _uhlmann_fidelity(J_carrier, J_oracle)
    one_minus_fe = float(max(0.0, 1.0 - F_pro))

    # Choi trace distance = 1/2 * trace-norm(J_carrier - J_oracle); trace-norm of a Hermitian
    # matrix is sum|eigenvalues|.
    diff = J_carrier - J_oracle
    diff = 0.5 * (diff + diff.conj().T)
    eig = np.linalg.eigvalsh(diff)
    choi_tv = float(0.5 * np.sum(np.abs(eig)))
    return one_minus_fe, choi_tv


def _uhlmann_fidelity(rho, sigma) -> float:
    """Uhlmann state fidelity ``F = (Tr sqrt( sqrt(rho) sigma sqrt(rho) ))^2`` between two
    PSD trace-1 matrices (the ``joint_lindbladian._state_fidelity`` convention, numpy/CPU).
    Returns a real float in [0, 1]."""
    import numpy as np

    rho = 0.5 * (rho + rho.conj().T)
    sigma = 0.5 * (sigma + sigma.conj().T)
    wr, Vr = np.linalg.eigh(rho)
    wr = np.clip(wr.real, 0.0, None)
    sqrt_rho = (Vr * np.sqrt(wr)) @ Vr.conj().T
    inner = sqrt_rho @ sigma @ sqrt_rho
    inner = 0.5 * (inner + inner.conj().T)
    wi = np.linalg.eigvalsh(inner)
    wi = np.clip(wi.real, 0.0, None)
    sqrt_sum = float(np.sum(np.sqrt(wi)))
    return float(sqrt_sum * sqrt_sum)


# --------------------------------------------------------------------------- #
# Channel-window builder (GPU production path; raises if not dense-checkable).  #
# --------------------------------------------------------------------------- #
class _ChannelNotDenseCheckable(Exception):
    """Raised when a substep/program cannot be densely certified (over-cap / record-bearing /
    multi-substep). The caller turns this into an honest ``executed: False`` (NOT a false
    "passed")."""


def _build_carrier_channel_window(
    schedule: Any,
    execution: dict[str, Any],
    *,
    device: str,
    dense_channel_max_dim: int = _DENSE_CHANNEL_MAX_DIM,
):
    """Build the carrier's REALIZED within-substep window superop (first-order MCWF
    unraveling: no-jump Kraus ``I - 1/2 dt c^dag c`` + jump Kraus ``sqrt(dt) c``, on the
    connected-cluster joint-Hamiltonian gate) AND the INDEPENDENT oracle Kraus
    ``assemble_substep_channel(H_list, c_list, dt)`` for the ONE channel-checkable substep.

    Reuses the carrier's OWN term->operator builders so the cert checks the carrier's actual
    dynamics, but the ORACLE is the sum-all joint ``expm(L dt)`` -- NEVER the carrier's
    grouping. Raises ``_ChannelNotDenseCheckable`` when the schedule is not a single small
    Hamiltonian+collapse substep.

    This path requires CUDA because it calls ``assemble_substep_channel`` and
    the carrier's torch helpers.
    """
    import torch

    from ..carrier.joint_lindbladian import assemble_substep_channel
    from ..frontend.axis1_carrier_program import (
        AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT,
        axis1_carrier_program_manifest,
    )

    program = axis1_carrier_program_manifest(
        schedule, backend_contract=AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT
    )
    substeps = [
        s
        for s in program["program"]["substeps"]
        if str(s.get("substep_kind")) not in {"measurement", "reset"}
        and any(
            str(t["kind"]) in {"hamiltonian", "collapse"} for t in s.get("terms", ())
        )
    ]
    if len(substeps) != 1:
        raise _ChannelNotDenseCheckable(
            "channel_certification_requires_exactly_one_hamiltonian_collapse_substep"
        )
    substep = substeps[0]
    if any(str(s.get("substep_kind")) in {"measurement", "reset"} for s in program["program"]["substeps"]):
        raise _ChannelNotDenseCheckable("channel_certification_excludes_record_bearing_substeps")

    local_dims = tuple(int(d) for d in execution["local_dims"])
    dt_ns = float(substep["dt_ns"])

    # --- gather the window support and dimension -------------------------------- #
    support: set[int] = set()
    for term in substep.get("terms", ()):
        for q in term.get("support", ()):
            support.add(int(q))
    window_qubits = tuple(sorted(support))
    dim = 1
    for q in window_qubits:
        dim *= int(local_dims[q])
    if dim > int(dense_channel_max_dim):
        raise _ChannelNotDenseCheckable("channel_checkable_substep_too_large_to_densely_check")

    lift_fn = _make_lift_fn(window_qubits, local_dims, dim)

    # --- oracle H_list / c_list on the window (sum-all joint expm) -------------- #
    H_list, c_list = _window_oracle_operators(
        substep, window_qubits, local_dims, dt_ns, lift_fn, device=device
    )
    if not H_list and not c_list:
        raise _ChannelNotDenseCheckable("channel_certification_substep_has_no_generators")

    oracle_kraus = [
        k.detach().cpu().numpy()
        for k in assemble_substep_channel(H_list, c_list, dt_ns, device=device)
    ]

    # --- carrier realized first-order MCWF window superop ----------------------- #
    carrier_superop = _carrier_first_order_window_superop(
        substep, window_qubits, local_dims, dt_ns, dim, lift_fn, device=device
    )
    return {
        "carrier_superop": carrier_superop,
        "oracle_kraus": oracle_kraus,
        "dim": int(dim),
    }


def _make_lift_fn(window_qubits, local_dims, dim):
    """Return a closure that lifts a |op_support|-site operator to the window via kron with
    identities, then permutes legs into window order (mirrors the carrier's own lift logic).
    Shared by the channel-window builder AND the level-population oracle."""
    import numpy as np

    def _lift(op_small, op_support):
        op_small = np.asarray(op_small, dtype=np.complex128)
        op_support = tuple(int(q) for q in op_support)
        order = tuple(op_support) + tuple(q for q in window_qubits if q not in op_support)
        rest = [q for q in window_qubits if q not in op_support]
        rest_dim = 1
        for q in rest:
            rest_dim *= int(local_dims[q])
        full = (
            np.kron(op_small, np.eye(rest_dim, dtype=np.complex128))
            if rest_dim > 1
            else op_small
        )
        leg = [int(local_dims[q]) for q in order]
        n = len(order)
        full = full.reshape(leg + leg)
        cur = {q: i for i, q in enumerate(order)}
        perm = [cur[q] for q in window_qubits] + [n + cur[q] for q in window_qubits]
        full = np.transpose(full, perm).reshape(dim, dim)
        return full

    return _lift


def _window_oracle_operators(
    substep, window_qubits, local_dims, dt_ns, lift_fn, *, device: str
):
    """Build the INDEPENDENT oracle ``(H_list, c_list)`` on the window for one dynamics
    substep from the per-term PHYSICS DEFINITIONS — ``_hamiltonian_matrix_for_term`` per
    Hamiltonian term, ``_collapse_operator`` per collapse term — each lifted to the window.
    The oracle sum-alls these into ONE ``expm(L dt)`` (``assemble_substep_channel``).

    ANTI-CIRCULAR (FAITHFULNESS rule I): the oracle is built from the per-term operators,
    NOT from ``_hamiltonian_group_gates`` (the carrier's GROUPING, which is the object under
    test). A wrong / no-op / mis-grouped carrier Hamiltonian is therefore CAUGHT — the
    earlier ``H_cluster = (i/dt) logm(carrier gate)`` form derived the oracle FROM the
    carrier's own gates, so a broken grouping would have produced a matching broken oracle
    (a false pass). ``_hamiltonian_matrix_for_term`` is the per-term builder, independently
    certified correct vs hand-typed literature references (round-2 cert 2/6); only the
    GROUPING is under test here, not the per-term physics."""
    import torch

    from ..frontend.axis1_mcwf_mps_execution import (
        _collapse_operator,
        _hamiltonian_matrix_for_term,
    )

    H_list = []
    c_list = []
    for term in substep.get("terms", ()):
        kind = str(term["kind"])
        if kind == "hamiltonian":
            support = tuple(int(q) for q in term["support"])
            H_small = _hamiltonian_matrix_for_term(
                term, support=support, local_dims=local_dims, device=device
            )
            H_full = lift_fn(H_small.detach().cpu().numpy(), support)
            H_list.append(torch.as_tensor(H_full, dtype=torch.complex128, device=device))
        elif kind == "collapse" and abs(float(term.get("coefficient", 0.0))) > 0.0:
            tsupport = tuple(int(q) for q in term["support"])
            c_small = _collapse_operator(term, local_dim=local_dims[tsupport[0]], device=device)
            c_full = lift_fn(c_small.detach().cpu().numpy(), tsupport)
            c_list.append(torch.as_tensor(c_full, dtype=torch.complex128, device=device))
    return H_list, c_list


def _carrier_first_order_window_superop(
    substep, window_qubits, local_dims, dt_ns, dim, lift_fn, *, device: str
):
    """The carrier's REALIZED within-substep CPTP map as a column-stacking superop, built
    EXACTLY as the MCWF trajectory ensemble realizes it: the connected-cluster joint
    Hamiltonian unitary U, then the first-order quantum-jump Kraus set
    ``{ U_nojump = I - 1/2 dt sum_k c_k^dag c_k , sqrt(dt) c_k }`` (this is the ensemble-
    averaged channel the sampled trajectories estimate; averaging over outcomes gives the
    deterministic CPTP map, NO sampling). Returns the (D^2, D^2) column-stacking superop S
    with ``vec(E(rho)) = S vec(rho)``.
    """
    import numpy as np

    from ..frontend.axis1_mcwf_mps_execution import (
        _collapse_operator,
        _hamiltonian_group_gates,
    )

    # Hamiltonian: product of the connected-cluster joint gates (they act on disjoint
    # clusters => commute => ordered product is the window unitary).
    U = np.eye(dim, dtype=np.complex128)
    for gate_rec in _hamiltonian_group_gates(
        substep, dt_ns=dt_ns, local_dims=local_dims, device=device
    ):
        g = gate_rec["gate"].detach().cpu().numpy()
        cluster = tuple(int(q) for q in gate_rec["support"])
        U = lift_fn(g, cluster) @ U

    # First-order quantum-jump Kraus on the window.
    kraus = []
    sum_cdc = np.zeros((dim, dim), dtype=np.complex128)
    jump_ops = []
    for term in substep.get("terms", ()):
        if str(term["kind"]) != "collapse":
            continue
        if abs(float(term.get("coefficient", 0.0))) <= 0.0:
            continue
        tsupport = tuple(int(q) for q in term["support"])
        c_small = _collapse_operator(term, local_dim=local_dims[tsupport[0]], device=device)
        c_full = lift_fn(c_small.detach().cpu().numpy(), tsupport)
        jump_ops.append(c_full)
        sum_cdc = sum_cdc + c_full.conj().T @ c_full
    K_nojump = np.eye(dim, dtype=np.complex128) - 0.5 * float(dt_ns) * sum_cdc
    # The Hamiltonian unitary precedes the jump structure in the microstep (state evolved
    # under U, then jump competition); compose the channel as jumps . U.
    kraus.append(K_nojump @ U)
    for c_full in jump_ops:
        kraus.append((float(dt_ns) ** 0.5) * c_full @ U)

    # Build the column-stacking superop S = sum_k conj(K) (x) K.
    S = np.zeros((dim * dim, dim * dim), dtype=np.complex128)
    for K in kraus:
        S = S + np.kron(K.conj(), K)
    return S


# --------------------------------------------------------------------------- #
# Dense joint-L level-population reference.                                    #
# --------------------------------------------------------------------------- #
def _dense_jointL_level_distribution(
    schedule: Any,
    execution: dict[str, Any],
    *,
    device: str,
    dense_channel_max_dim: int = _DENSE_CHANNEL_MAX_DIM,
) -> dict[tuple[int, ...], float]:
    """The readout-INDEPENDENT LEVEL-population oracle: the distribution over recorded
    level-tuples obtained by evolving the initial level state through the program with the
    DESIGNATED INDEPENDENT ORACLE ``assemble_substep_channel`` per dynamics substep, applying
    resets, and reading the level-basis DIAGONAL (populations) at each measurement substep's
    targets -- EXACTLY the sites + order the carrier records.

    Returns ``{tuple(levels): probability}`` over the joint sequence of measured levels (one
    entry per measurement substep target, concatenated in substep order). A no-op leaves the
    populations at the initial level, so this oracle catches it.

    Algorithm (faithful to the carrier's projective level-readout semantics): maintain a list
    of (rho, level_record_prefix, branch_probability) branches over the FULL system Hilbert
    space (dim = prod local_dims). For each substep:
      * dynamics substep -> advance every branch's rho by the joint-L channel on the
        connected window (lifted to the full space);
      * reset substep -> apply the projective reset channel to every branch;
      * measurement substep -> for each target site, split each branch by the level
        populations at that site (diagonal of the reduced single-site rho), conditioning rho
        on each level (projector sandwich, renormalised) and appending the level to the
        prefix, weighting by the conditional population.
    Accumulate the final branches into the level-record distribution.

    This path requires CUDA because it calls ``assemble_substep_channel``.
    """
    import numpy as np
    import torch

    from ..carrier.joint_lindbladian import assemble_substep_channel
    from ..frontend.axis1_carrier_program import (
        AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT,
        axis1_carrier_program_manifest,
    )
    local_dims = tuple(int(d) for d in execution["local_dims"])
    initial_levels = tuple(int(x) for x in execution["initial_levels"])
    num_sites = len(local_dims)
    full_dim = 1
    for d in local_dims:
        full_dim *= int(d)
    if full_dim > int(dense_channel_max_dim):
        raise _ChannelNotDenseCheckable("level_checkable_program_too_large_to_densely_check")

    program = axis1_carrier_program_manifest(
        schedule, backend_contract=AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT
    )

    all_sites = tuple(range(num_sites))
    lift_fn = _make_lift_fn(all_sites, local_dims, full_dim)

    # site strides for the full row-major index (site 0 most-significant), matching the
    # carrier's index_from_digits convention (digit[0] is the leading site).
    strides = [1] * num_sites
    acc = 1
    for s in range(num_sites - 1, -1, -1):
        strides[s] = acc
        acc *= int(local_dims[s])

    def _single_site_projector_full(site: int, level: int):
        op = np.zeros((int(local_dims[site]), int(local_dims[site])), dtype=np.complex128)
        op[int(level), int(level)] = 1.0
        return lift_fn(op, (int(site),))

    # initial pure-state density matrix on the full space.
    idx0 = 0
    for s in range(num_sites):
        idx0 += strides[s] * int(initial_levels[s])
    rho0 = np.zeros((full_dim, full_dim), dtype=np.complex128)
    rho0[idx0, idx0] = 1.0

    # Each branch: (rho, level_prefix_tuple, branch_probability).
    branches: list[tuple[np.ndarray, tuple[int, ...], float]] = [(rho0, (), 1.0)]

    for substep in program["program"]["substeps"]:
        kind = str(substep.get("substep_kind"))
        if kind == "reset":
            # Projective reset to |0> per target (the carrier samples a level then resets to
            # the reset target vector |0>); as a channel this maps rho -> |0><0| on the site.
            new_branches = []
            for rho, prefix, w in branches:
                rho_new = rho
                for op in substep.get("operation_records", ()):
                    basis = _dense_reset_basis(str(op.get("name", "")))
                    if basis is None:
                        continue
                    for target in op.get("targets", ()):
                        site = int(target)
                        # reset to |0>: P0 rho P0 + sum_{l>0} |0><l| rho |l><0| ; equivalently
                        # trace out the site and re-prepare |0>. We implement the standard
                        # reset channel sum_l |0><l| rho |l><0| at the site.
                        dim_s = int(local_dims[site])
                        acc_rho = np.zeros((full_dim, full_dim), dtype=np.complex128)
                        for level in range(dim_s):
                            K = np.zeros((dim_s, dim_s), dtype=np.complex128)
                            K[0, level] = 1.0
                            Kf = lift_fn(K, (site,))
                            acc_rho = acc_rho + Kf @ rho_new @ Kf.conj().T
                        rho_new = acc_rho
                new_branches.append((rho_new, prefix, w))
            branches = new_branches
            continue

        if kind == "measurement":
            # Independently parse every operation record into per-target basis/reset facts.
            # The physical branch evolution below remains hand-built NumPy and shares no
            # carrier measurement/reset kernel.
            targets: list[int] = []
            target_bases: list[str] = []
            target_reset_after: list[bool] = []
            for op_record in substep.get("operation_records", ()):
                op_targets = [int(q) for q in op_record.get("targets", ())]
                op_keys = [str(key) for key in op_record.get("measurement_keys", ())]
                if len(op_keys) != len(op_targets):
                    raise _ChannelNotDenseCheckable(
                        "level_oracle_measurement_keys_do_not_match_targets"
                    )
                basis = str(op_record.get("basis", "Z")).upper()
                reset_requested = bool(
                    op_record.get("reset_after_measurement", False)
                )
                targets.extend(op_targets)
                target_bases.extend([basis] * len(op_targets))
                target_reset_after.extend([reset_requested] * len(op_targets))
            for target, target_basis, reset_after in zip(
                targets,
                target_bases,
                target_reset_after,
                strict=True,
            ):
                if target_basis not in {"X", "Z"}:
                    raise _ChannelNotDenseCheckable(
                        "level_oracle_measurement_supports_x_or_z_basis_only"
                    )
                dim_s = int(local_dims[target])
                Hf = None
                if target_basis == "X":
                    # Independent numpy H = (1/sqrt2)[[1,1],[1,-1]] on the {|0>,|1>} block,
                    # identity on leaked levels: rotate the X-target into the Z eigenbasis
                    # before the Z-level projection below. Non-reset branches rotate the
                    # conditioned state back before later substeps consume it.
                    Hloc = np.eye(dim_s, dtype=np.complex128)
                    inv = 1.0 / np.sqrt(2.0)
                    Hloc[0, 0] = inv
                    Hloc[0, 1] = inv
                    Hloc[1, 0] = inv
                    Hloc[1, 1] = -inv
                    Hf = lift_fn(Hloc, (int(target),))
                    branches = [
                        (Hf @ rho @ Hf.conj().T, prefix, w) for rho, prefix, w in branches
                    ]
                next_branches = []
                for rho, prefix, w in branches:
                    for level in range(dim_s):
                        P = _single_site_projector_full(target, level)
                        rho_cond = P @ rho @ P.conj().T
                        branch_trace = np.trace(rho_cond)
                        p_level = float(branch_trace.real)
                        if (
                            not math.isfinite(p_level)
                            or not math.isfinite(float(branch_trace.imag))
                            or p_level < 0.0
                        ):
                            raise ValueError(
                                "level oracle measurement branch trace must be finite "
                                "and nonnegative"
                            )
                        if p_level == 0.0:
                            continue
                        rho_norm = rho_cond / p_level
                        if not np.all(np.isfinite(rho_norm)):
                            raise ValueError(
                                "level oracle conditioned measurement state must be finite"
                            )
                        if reset_after:
                            # The projection branch is in the rotated frame for X.
                            # Re-prepare the reset target in the original frame:
                            # |0> for Z and |+> for X.
                            target_vector = np.zeros(dim_s, dtype=np.complex128)
                            if target_basis == "Z":
                                target_vector[0] = 1.0
                            else:
                                target_vector[0] = inv
                                target_vector[1] = inv
                            from_vector = np.zeros(dim_s, dtype=np.complex128)
                            from_vector[int(level)] = 1.0
                            Kr = np.outer(target_vector, from_vector.conj())
                            Krf = lift_fn(Kr, (int(target),))
                            rho_norm = Krf @ rho_norm @ Krf.conj().T
                            reset_trace = np.trace(rho_norm)
                            tr = float(reset_trace.real)
                            if (
                                not math.isfinite(tr)
                                or not math.isfinite(float(reset_trace.imag))
                                or tr <= 0.0
                            ):
                                raise ValueError(
                                    "level oracle reset trace must be finite and greater "
                                    "than zero"
                                )
                            rho_norm = rho_norm / tr
                            if not np.all(np.isfinite(rho_norm)):
                                raise ValueError(
                                    "level oracle normalized reset state must be finite"
                                )
                        elif Hf is not None:
                            rho_norm = Hf @ rho_norm @ Hf.conj().T
                        next_branches.append(
                            (rho_norm, prefix + (int(level),), float(w * p_level))
                        )
                branches = next_branches
            continue

        # dynamics substep (hamiltonian / collapse): advance every branch by the joint-L
        # channel on the connected window, lifted to the full space.
        if not _substep_has_dynamics(substep):
            continue
        dt_ns = float(substep["dt_ns"])
        window_qubits = _dynamics_window_qubits(substep)
        if not window_qubits:
            continue
        win_dim = 1
        for q in window_qubits:
            win_dim *= int(local_dims[q])
        if win_dim > int(dense_channel_max_dim):
            raise _ChannelNotDenseCheckable("level_checkable_program_too_large_to_densely_check")
        win_lift = _make_lift_fn(window_qubits, local_dims, win_dim)
        H_list, c_list = _window_oracle_operators(
            substep, window_qubits, local_dims, dt_ns, win_lift, device=device
        )
        if not H_list and not c_list:
            continue
        oracle_kraus = [
            k.detach().cpu().numpy()
            for k in assemble_substep_channel(H_list, c_list, dt_ns, device=device)
        ]
        # lift each window Kraus to the full space (kron-and-permute), then apply.
        full_kraus = [lift_fn(K, window_qubits) for K in oracle_kraus]
        new_branches = []
        for rho, prefix, w in branches:
            rho_new = np.zeros((full_dim, full_dim), dtype=np.complex128)
            for K in full_kraus:
                rho_new = rho_new + K @ rho @ K.conj().T
            new_branches.append((rho_new, prefix, w))
        branches = new_branches

    dist: dict[tuple[int, ...], float] = {}
    for _rho, prefix, w in branches:
        if not prefix:
            continue
        dist[prefix] = dist.get(prefix, 0.0) + float(w)
    return dist


def _substep_has_dynamics(substep: dict[str, Any]) -> bool:
    for term in substep.get("terms", ()):
        kind = str(term["kind"])
        if kind == "hamiltonian":
            return True
        if kind == "collapse" and abs(float(term.get("coefficient", 0.0))) > 0.0:
            return True
    return False


def _dynamics_window_qubits(substep: dict[str, Any]) -> tuple[int, ...]:
    support: set[int] = set()
    for term in substep.get("terms", ()):
        kind = str(term["kind"])
        if kind == "hamiltonian" or (
            kind == "collapse" and abs(float(term.get("coefficient", 0.0))) > 0.0
        ):
            for q in term.get("support", ()):
                support.add(int(q))
    return tuple(sorted(support))


__all__ = [
    "dense_jointL_record_certification",
    "restricted_acceptance_policy",
]
