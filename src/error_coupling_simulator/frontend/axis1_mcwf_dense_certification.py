from __future__ import annotations

"""Axis-1 W-B dense-oracle acceptance certification for the MCWF/MPS carrier.

Replaces the previously-INERT ``_restricted_acceptance_policy`` (``accepted = residual_ok
AND seed_explicit``, which reduced to "a seed was supplied" because
``total_probability_residual`` is 0 BY CONSTRUCTION) with a gate that certifies the
carrier's ACTUAL output against the INDEPENDENT joint-L oracle
``forward.joint_lindbladian.assemble_substep_channel`` (sum-all -> one ``expm(L dt)``,
built from the per-term physics ``_hamiltonian_matrix_for_term`` -- NEVER the carrier's own
``_hamiltonian_group_gates``, so a wrong/no-op grouping is CAUGHT, not mirrored). Three
certification paths + a gross/strict multi-tier gate:

  ADD 1 -- a readout-INDEPENDENT LEVEL-record cert. Oracle = the level POPULATIONS of the
    dense joint-L channel: evolve ``rho0`` (the initial level product state) through the
    program with the DESIGNATED INDEPENDENT ORACLE ``assemble_substep_channel(H, c, dt)``
    (sum-all -> one ``expm(L dt)`` -- NEVER the carrier's grouping) for each dynamics
    substep, apply resets as projective-reset channels, and read the level-basis DIAGONAL
    (populations) at each measurement substep's targets, accumulating the joint distribution
    over the recorded level-tuples exactly as the carrier records them. Carrier level
    distribution = ``level_record_counts / sum``. Metric TV = 1/2 ||p-q||_1 + the same
    Hoeffding finite-shot CI. Compares LEVEL POPULATIONS, so no leakage-readout model is
    needed; a no-op leaves ``rho0`` => populations sit at the initial level => caught.
    Routed when ``execution.get("level_records")`` is present (BEFORE the qubit-record path).

  ADD 2 -- a GROSS/STRICT gate split. At the carrier's default ``microstep_count=1`` the
    first-order MCWF has a REAL finite-step error (channel ``1-F_e ~ 1e-2``) -- that is
    CORRECT, not a bug, and must NOT be rejected as broken, while a no-op is ``O(1)``. So
    ``accepted_for_restricted_execution`` gates on a GROSS disagreement only
    (channel ``1-F_e <= tau_gross = 1e-1``; record/level ``TV <= tau_gross + sampling CI``),
    so a correct ``m=1`` run PASSES and a no-op/wrong-branch FAILS;
    ``accepted_for_exact_dense_probability_evidence`` keeps the STRICT gate
    (``1-F_e <= 1e-6`` / exact-branch ``TV ~ 0``). Both the strict value AND the gross
    pass/fail are reported.

  ADD 3 -- an HONEST "uncertified" fallback for TRUE OVERCAP ONLY. A run the cert CAN check
    MUST be certified (so no-ops are caught). Only a genuinely-uncheckable run (window
    Hilbert dim > cap, or ``requires_scalable_backend``) falls back to
    ``accepted_for_restricted_execution=True`` with ``dense_certification_status:
    skipped_overcap_*`` and ``accepted_for_exact_dense_probability_evidence=False``. A cert
    that EXECUTED and FAILED its GROSS gate => REJECT (never fall back). Never inert-accept a
    checkable run.

Field-standard metrics ONLY (``1-F_e`` process infidelity, Choi trace distance, TV
distance), conventions carried with the numbers. The independent oracle is NEVER the
carrier's own grouping.

GPU note: ``joint_lindbladian`` is HARD CUDA-only (``_require_cuda`` rejects CPU), so the
real GPU cert (Claude runs) uses it directly via ``dense_jointL_record_certification(...,
device="cuda")``. The committed CPU red-test (``red_test.py``) exercises the SAME gate
DECISION LOGIC against an INDEPENDENT numpy/scipy reimplementation of the identical
column-stacking Liouvillian + level-population oracle (NOT the carrier's grouping), to prove
the gate is now LIVE -- and that correct LEVEL runs PASS while no-ops/wrong-branches FAIL --
without a GPU run.
"""

from typing import Any

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
# Epistemic class (c) -- justified: post-W-A the realized first-order CHANNEL finite-step
# error at microstep_count=1 is at most a few * 1e-2 (1-F_e; S2/S3 cert baseline), which is
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
# Record/level STRICT path tau: exact-branch (un-sampled) Born populations agree with the
# dense oracle to the matrix_exp/Choi floor; the sampled MCWF path is a finite-shot
# estimator, so the strict record gate is met as TV <= tau_rec at a dense-checkable substep,
# with a Hoeffding finite-shot CI surfaced for the sampled path.
_RECORD_TV_GATE = 1.0e-6
# Sampled-path finite-shot allowance: a per-bin Hoeffding half-width at this confidence is
# added to the TV gate so a CORRECT sampled carrier is not rejected for shot noise alone,
# while a wrong-branch carrier (TV >> shot noise) is still rejected.
_RECORD_SAMPLING_CONFIDENCE = 0.999
# Normalization invariant gate (the RENAMED total_probability_residual role): a sanity
# invariant sum(record-frequencies) == 1, NOT a distinguishability metric. Matches the
# carrier's _TOTAL_PROBABILITY_RESIDUAL_GATE == 1e-12.
_NORMALIZATION_INVARIANT_GATE = 1.0e-12
# Window Hilbert dimension above which the dense check is forbidden (true over-cap). A few
# hundred (the brief's "<= a few hundred"); 3^5 = 243 fits, 3^6 = 729 does not. The leakage
# fixtures are 1-2 sites of dim 3-4 (total dim <= 9), all densely checkable.
_DENSE_CHANNEL_MAX_DIM = 256
# Qubit count above which the INDEPENDENT dense Born record oracle
# (axis1_measurement_record_evidence_manifest) is forbidden: it builds an exact 2^N density
# matrix and is itself capped at 8 qubits (axis1_record_evidence._validate_record_evidence_
# schedule). A run above this cap (e.g. the d3 q17 XZZX schedule) is a RESTRICTED over-cap
# execution, NOT a failure -- routed honestly without ever building a 2^N DM.
_RECORD_EVIDENCE_QUBIT_CAP = 8


# --------------------------------------------------------------------------- #
# Piece 1: the MCWF-carrier dense-oracle certification builder.                 #
# --------------------------------------------------------------------------- #
def dense_jointL_record_certification(
    schedule: Any,
    execution: dict[str, Any],
    program: dict[str, Any],
    *,
    device: str = "cuda",
    process_infidelity_gate: float = _PROCESS_INFIDELITY_GATE,
    record_tv_gate: float = _RECORD_TV_GATE,
    gross_gate: float = _GROSS_GATE,
    record_sampling_confidence: float = _RECORD_SAMPLING_CONFIDENCE,
    dense_channel_max_dim: int = _DENSE_CHANNEL_MAX_DIM,
    _oracle_record_probabilities=None,
    _oracle_level_distribution=None,
) -> dict[str, Any]:
    """Certify the MCWF carrier's within-substep output vs the INDEPENDENT joint-L oracle.

    Routing (fail-closed honest ``executed: False`` reasons FIRST), then ONE metric
    comparison vs an oracle independent of the carrier's grouping, returning
    ``{executed, passed, passed_gross, comparison_outcome_is_metric, metric, value, gate,
    gross_gate, ...}``:

      1. over-cap (``requires_scalable_backend``)        -> executed: False (honest).
      2. LEVEL records present (leakage qudit outcomes)  -> ``_certify_level_path``
         (readout-INDEPENDENT level-population oracle). ADD 1.
      3. qubit measurement records present               -> ``_certify_record_path``.
      4. no records (Hamiltonian + collapse substep)     -> ``_certify_channel_path``.

    Args:
      schedule  : the ``SubstepSchedule`` (the same object the carrier consumed). Used to
                  build the INDEPENDENT dense oracle.
      execution : the carrier ``mps_execution`` dict (``level_records``,
                  ``level_record_counts``, ``record_probabilities``, ``measurement_records``,
                  ``measurement_keys``, ``trajectory_sampling``, ``local_dims``,
                  ``initial_levels`` ...).
      program   : the carrier program manifest (``requires_scalable_backend`` over-cap flag).
      device    : cuda (the joint-L oracle stack is GPU-only); the CPU red-test injects
                  numpy oracles via the explicit ``_oracle_*`` branches.

    Returns the certification dict consumed by ``restricted_acceptance_policy``.
    """
    # --- (1) fail-closed honest over-cap reason FIRST. ----------------------------- #
    if bool(program.get("requires_scalable_backend", False)):
        return {
            "executed": False,
            "passed": False,
            "passed_gross": False,
            "reason": "schedule_contains_scalable_required_rows",
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        }

    sampling = execution.get("trajectory_sampling", {})
    sampled = str(sampling.get("mode", "")).startswith("sampled")
    seed_explicit = bool(sampling.get("rng_seed_was_explicit", False))
    trajectory_count = int(sampling.get("trajectory_count", 0) or 0)

    has_level_records = bool(execution.get("level_records"))
    has_records = bool(execution.get("measurement_keys"))

    # --- (2) LEVEL-record path (leakage qudit outcomes) -- ADD 1. ------------------ #
    # Routed BEFORE the qubit-record path: leakage schedules carry BOTH measurement_keys
    # and level_records, but the readout-INDEPENDENT level-population comparison is the
    # faithful (and the only oracle-backed) check for a qudit run.
    if has_level_records:
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
            device=device,
            record_tv_gate=float(record_tv_gate),
            gross_gate=float(gross_gate),
            record_sampling_confidence=float(record_sampling_confidence),
            dense_channel_max_dim=int(dense_channel_max_dim),
            sampled=sampled,
            trajectory_count=trajectory_count,
            _oracle_level_distribution=_oracle_level_distribution,
        )

    # --- (3) qubit measurement-record path. ---------------------------------------- #
    if has_records:
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
            gross_gate=float(gross_gate),
            record_sampling_confidence=float(record_sampling_confidence),
            sampled=sampled,
            trajectory_count=trajectory_count,
            _oracle_record_probabilities=_oracle_record_probabilities,
        )

    # --- (4) no measurement records => channel-checkable substep. ------------------ #
    return _certify_channel_path(
        schedule,
        execution,
        device=device,
        process_infidelity_gate=float(process_infidelity_gate),
        gross_gate=float(gross_gate),
        dense_channel_max_dim=int(dense_channel_max_dim),
    )


# --------------------------------------------------------------------------- #
# ADD 1: the LEVEL-record certification path.                                   #
# --------------------------------------------------------------------------- #
def _certify_level_path(
    schedule: Any,
    execution: dict[str, Any],
    *,
    device: str,
    record_tv_gate: float,
    gross_gate: float,
    record_sampling_confidence: float,
    dense_channel_max_dim: int,
    sampled: bool,
    trajectory_count: int,
    _oracle_level_distribution=None,
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

    ``_oracle_level_distribution`` is an injection seam used ONLY by the CPU red-test to
    supply a numpy level-population oracle (a ``{tuple(levels): prob}`` dict) independent of
    the carrier; in production it is ``None`` and the real GPU oracle is built via
    ``_dense_jointL_level_distribution`` (joint-L ``expm`` per substep).
    """
    carrier_level_records = [tuple(int(x) for x in r) for r in execution.get("level_records", ())]
    carrier_counts = [int(c) for c in execution.get("level_record_counts", ())]
    total_counts = int(sum(carrier_counts))
    if total_counts <= 0:
        return {
            "executed": False,
            "passed": False,
            "passed_gross": False,
            "reason": "level_record_counts_empty",
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        }
    carrier_dist = {
        rec: float(cnt) / float(total_counts)
        for rec, cnt in zip(carrier_level_records, carrier_counts)
    }

    if _oracle_level_distribution is None:
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
        oracle_schema = (
            "error_coupling_simulator.carrier.joint_lindbladian."
            "assemble_substep_channel:level_populations"
        )
    else:
        oracle_dist = {
            tuple(int(x) for x in k): float(v)
            for k, v in dict(_oracle_level_distribution).items()
        }
        oracle_schema = "cpu_red_test_independent_numpy_level_population_oracle"

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

    # STRICT (exact-dense-evidence) gate is TIGHT — NOT CI-loosened: exact-dense evidence is
    # only claimable for an exact-branch (un-sampled) match, never from finite-shot samples
    # (the CI loosens ONLY the gross/restricted tier below). A no-op at small N therefore fails
    # strict, and a correct SAMPLED run is honestly "restricted-accepted, not exact-dense".
    strict_effective_gate = float(record_tv_gate)
    gross_effective_gate = _gross_record_tv_budget(sampling_halfwidth)
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
        "gross_gate": float(_GROSS_RECORD_TV_GATE),
        "gross_gate_ceiling": float(_GROSS_RECORD_TV_CEILING),
        "sampling_finite_shot_halfwidth": float(sampling_halfwidth),
        "effective_gate_including_sampling_ci": strict_effective_gate,
        "gross_effective_gate_including_sampling_ci": float(gross_effective_gate),
        "sampling_ci_method": "per_bin_two_sided_hoeffding_capped_at_gross_tv_ceiling",
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
    _oracle_record_probabilities=None,
) -> dict[str, Any]:
    """Qubit measurement-record cert: carrier record_probabilities vs the INDEPENDENT
    dense Born record oracle, scored by TV = 1/2 ||p-q||_1 (+ Hoeffding finite-shot CI).

    ``_oracle_record_probabilities`` is an injection seam used ONLY by the CPU red-test to
    supply a numpy/scipy Born oracle independent of the carrier; in production it is ``None``
    and the real GPU oracle ``axis1_measurement_record_evidence_manifest`` is called (the
    SAME oracle qt_mps uses, NEVER the carrier's own grouping).
    """
    carrier_records = [list(r) for r in execution.get("measurement_records", ())]
    carrier_probs = [float(x) for x in execution.get("record_probabilities", ())]

    # Honest over-cap routing: the INDEPENDENT dense Born record oracle
    # (axis1_measurement_record_evidence_manifest) builds an exact 2^N density matrix and is
    # capped at AXIS1_RECORD_EVIDENCE_QUBIT_CAP qubits. A genuinely-over-cap run (e.g. the
    # d3 q17 XZZX schedule) is NOT a failure and must NOT attempt a 2^N DM build: return the
    # over-cap reason so the acceptance policy treats it as a RESTRICTED over-cap execution
    # (mirrors the level path's level_checkable_program_too_large_to_densely_check). This is
    # checked BEFORE the oracle call so no 2^17 DM is ever constructed.
    # NOTE (belt-and-suspenders): for any measurement-bearing schedule the execution always
    # records level tuples, so certification routes to the LEVEL path FIRST, where the
    # pre-existing _DENSE_CHANNEL_MAX_DIM (256) guard in _dense_jointL_level_distribution is
    # what actually caps q17 (before rho0 is allocated). This record-path guard is the
    # backstop for the (currently unreachable) no-level-records case, not the q17 hot path.
    num_sites = len(execution.get("local_dims", ()))
    if _oracle_record_probabilities is None and num_sites > _RECORD_EVIDENCE_QUBIT_CAP:
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

    if _oracle_record_probabilities is None:
        try:
            from .axis1_record_evidence import (
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
        oracle_records = [list(r) for r in dense_record["measurement_records"]]
        oracle_probs = [float(x) for x in dense_record["record_probabilities"]]
        dense_schema = dense.get("schema")
        dense_hash = dense.get("content_hash")
    else:
        oracle_records = carrier_records
        oracle_probs = [float(x) for x in _oracle_record_probabilities]
        dense_schema = "cpu_red_test_independent_numpy_born_oracle"
        dense_hash = None

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

    # STRICT (exact-dense-evidence) gate is TIGHT — NOT CI-loosened: exact-dense evidence is
    # only claimable for an exact-branch (un-sampled) match, never from finite-shot samples
    # (the CI loosens ONLY the gross/restricted tier below). A no-op at small N therefore fails
    # strict, and a correct SAMPLED run is honestly "restricted-accepted, not exact-dense".
    strict_effective_gate = float(record_tv_gate)
    gross_effective_gate = _gross_record_tv_budget(sampling_halfwidth)
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
        "gross_gate": float(_GROSS_RECORD_TV_GATE),
        "gross_gate_ceiling": float(_GROSS_RECORD_TV_CEILING),
        "sampling_finite_shot_halfwidth": float(sampling_halfwidth),
        "effective_gate_including_sampling_ci": strict_effective_gate,
        "gross_effective_gate_including_sampling_ci": float(gross_effective_gate),
        "sampling_ci_method": "per_bin_two_sided_hoeffding_capped_at_gross_tv_ceiling",
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
    _carrier_superop=None,
    _oracle_kraus=None,
    _oracle_superop=None,
) -> dict[str, Any]:
    """Channel-checkable substep cert: carrier realized within-substep window superop vs
    the INDEPENDENT joint-L oracle ``assemble_substep_channel``, scored by process
    infidelity ``1-F_e`` (Choi-state Uhlmann fidelity, the project's
    ``composed_vs_joint_infidelity`` convention) + Choi trace distance.

    ``passed`` = STRICT gate (``1-F_e <= 1e-6``, exact-dense evidence); ``passed_gross`` =
    GROSS gate (``1-F_e <= tau_gross``, restricted acceptance) so a correct ``m=1`` run with
    a real finite-step error passes restricted acceptance while a no-op/wrong-generator
    fails.

    ``_carrier_superop`` / (``_oracle_kraus`` OR ``_oracle_superop``) are injection seams
    used ONLY by the CPU red-test; in production they are ``None`` and the real GPU path
    builds them via ``_build_carrier_channel_window`` + ``assemble_substep_channel``.
    """
    if _carrier_superop is None or (_oracle_kraus is None and _oracle_superop is None):
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
        oracle_superop = None
        oracle_dim = int(window["dim"])
    else:
        import numpy as np

        carrier_superop = np.asarray(_carrier_superop, dtype=np.complex128)
        if _oracle_superop is not None:
            oracle_superop = np.asarray(_oracle_superop, dtype=np.complex128)
            oracle_kraus = None
            oracle_dim = int(round(oracle_superop.shape[-1] ** 0.5))
        else:
            oracle_kraus = [np.asarray(k, dtype=np.complex128) for k in _oracle_kraus]
            oracle_superop = None
            oracle_dim = int(oracle_kraus[0].shape[-1])

    one_minus_fe, choi_tv = _process_infidelity_and_choi_distance(
        carrier_superop, oracle_kraus, dim=oracle_dim, oracle_superop=oracle_superop
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
# Piece 2: the PATCHED restricted-acceptance gate (gross/strict split).         #
# --------------------------------------------------------------------------- #
def restricted_acceptance_policy(
    *,
    execution: dict[str, Any],
    certification: dict[str, Any],
    program: dict[str, Any],
    rng_seed: int | None,
    trajectory_count: int,
) -> dict[str, Any]:
    """The PATCHED ``_restricted_acceptance_policy``.

    Replaces the INERT
        accepted = residual_ok AND seed_explicit          # <=> seed supplied (INERT)
    with the gross/strict dense-cert form
        accepted_for_restricted_execution =
            normalization_invariant_ok
            AND ( (dense_executed AND dense_passed_gross)   # GROSS gate
                  OR honest-true-overcap fallback )
            AND (seed_explicit if the sampled path is being accepted as evidence)
        accepted_for_exact_dense_probability_evidence =
            accepted AND not sampled AND dense_executed AND dense_passed (STRICT gate).

    A correct ``microstep_count=1`` run (real finite-step error, channel ``1-F_e ~ 1e-2`` /
    sampled-level ``TV`` small) PASSES the GROSS gate => restricted-accepted. A no-op /
    wrong-branch / wrong-generator FAILS the gross gate => rejected. A genuinely-uncheckable
    TRUE-OVERCAP run falls back to restricted (never exact-dense). A cert that EXECUTED and
    FAILED the gross gate => REJECT (no fallback).

    Keeps ``total_probability_residual`` but RENAMES its ROLE to ``normalization_invariant``
    (a sum-frequencies sanity invariant, NOT a distinguishability metric). Sets
    ``comparison_outcome_is_metric: True`` ONLY where a real TV / 1-F_e / Choi metric was
    computed.
    """
    normalization_invariant = float(execution["total_probability_residual"])
    normalization_invariant_ok = normalization_invariant <= _NORMALIZATION_INVARIANT_GATE
    seed_explicit = rng_seed is not None

    sampling = execution.get("trajectory_sampling", {})
    sampled = str(sampling.get("mode", "")).startswith("sampled")
    requires_scalable = bool(program.get("requires_scalable_backend", False))

    dense_executed = bool(certification.get("executed", False))
    dense_passed_strict = bool(certification.get("passed", False))
    # Default passed_gross to the strict decision when a cert omits it (channel/record/level
    # certs in this module always set it; the fallback keeps older cert dicts safe).
    dense_passed_gross = bool(certification.get("passed_gross", dense_passed_strict))
    cert_metric_real = bool(certification.get("comparison_outcome_is_metric", False))
    dense_status = _dense_certification_status(certification)

    # The GROSS positive-evidence path: a real dense-oracle metric comparison passed the
    # GROSS gate. (For a sampled path the cert already folds the rng-seed requirement into
    # its own executed/passed decision, so an unseeded sampled run yields executed=False.)
    dense_evidence_gross = bool(dense_executed and dense_passed_gross)
    # The STRICT exact-dense evidence path: the same comparison passed the STRICT gate.
    dense_evidence_strict = bool(dense_executed and dense_passed_strict)

    # ADD 3 -- honest TRUE-OVERCAP fallback: ONLY a genuinely-uncheckable run (the window is
    # too large to densely check, or the schedule requires the scalable backend) stays a
    # RESTRICTED over-cap execution -- NEVER a falsely-"passed" certification, and NEVER an
    # inert-accept of a checkable run. A cert that EXECUTED and FAILED its gross gate does
    # NOT reach here (dense_status == "failed").
    overcap_restricted = bool(
        normalization_invariant_ok
        and dense_status == "skipped_overcap_dense_fallback_forbidden"
    )

    # The gate. A sampled path accepted as EMPIRICAL evidence still requires the seed
    # (reproducibility); when accepted via a passed dense metric the seed requirement is
    # already enforced inside the cert.
    sampled_evidence_seed_ok = bool(seed_explicit or not sampled)
    accepted = bool(
        normalization_invariant_ok
        and (dense_evidence_gross or overcap_restricted)
        and sampled_evidence_seed_ok
    )

    blockers: list[str] = []
    if not normalization_invariant_ok:
        blockers.append("normalization_invariant_exceeds_gate")
    if not dense_evidence_gross and not overcap_restricted:
        blockers.append(f"dense_jointL_certification:{dense_status}")
    if sampled and not seed_explicit:
        blockers.append("sampled_trajectory_rng_seed_not_explicit")
    if requires_scalable:
        blockers.append("overcap_large_code_policy_not_established")
    blockers.extend(
        [
            "production_error_control_policy_not_established",
            "multilevel_leakage_error_control_not_established",
            "finite_step_error_bound_not_established",
        ]
    )

    return {
        "schema": "qec_twin.simulator.axis1_mcwf_mps_restricted_acceptance_policy.v2",
        "policy_role": "restricted_execution_acceptance_not_metric",
        "accepted_for_restricted_execution": accepted,
        "accepted_for_sampled_execution_evidence": bool(
            accepted and sampled and dense_evidence_gross
        ),
        # STRICT exact-dense evidence: only an un-sampled run that passes the STRICT gate.
        "accepted_for_exact_dense_probability_evidence": bool(
            accepted and not sampled and dense_evidence_strict
        ),
        "accepted_for_production_scalable_backend": False,
        "accepted_as_restricted_overcap_execution": overcap_restricted,
        "blocked_reason": None if accepted else (blockers[0] if blockers else None),
        "gross_strict_gate_split": {
            "gross_gate_role": "restricted_acceptance_gate_catches_gross_disagreement_no_op_wrong_branch",
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
            "comparison_object": certification.get("comparison_object"),
            "metric": certification.get("metric"),
            "metric_convention": certification.get("metric_convention"),
            "value": certification.get("value"),
            "gate": certification.get("gate"),
            "gross_gate": certification.get("gross_gate"),
            "choi_trace_distance": certification.get("choi_trace_distance"),
            "effective_gate_including_sampling_ci": certification.get(
                "effective_gate_including_sampling_ci"
            ),
            "gross_effective_gate_including_sampling_ci": certification.get(
                "gross_effective_gate_including_sampling_ci"
            ),
            "oracle": certification.get("oracle"),
            "oracle_role": certification.get("oracle_role"),
            "oracle_independent_of_carrier_grouping": certification.get(
                "oracle_independent_of_carrier_grouping"
            ),
            "readout_model_independent": certification.get("readout_model_independent"),
            # True ONLY where a real TV / 1-F_e / Choi metric was computed.
            "comparison_outcome_is_metric": cert_metric_real,
            "metric_epistemic_class": certification.get("metric_epistemic_class"),
            "gate_epistemic_class": certification.get("gate_epistemic_class"),
            "reason": certification.get("reason"),
        },
        "trajectory": {
            "mode": str(sampling.get("mode", "sampled_fixed_microstep_mcwf_trajectories")),
            "trajectory_count": int(trajectory_count),
            "rng_seed": None if rng_seed is None else int(rng_seed),
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
        "probability": {
            # RENAMED ROLE: a normalization sanity invariant (sum record frequencies == 1),
            # NOT a distinguishability metric. Kept for transparency; never gates correctness.
            "normalization_invariant": normalization_invariant,
            "normalization_invariant_gate": _NORMALIZATION_INVARIANT_GATE,
            "role": "normalization_sanity_invariant_not_distinguishability_metric",
            "legacy_field_name": "total_probability_residual",
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
    if bool(certification.get("executed", False)):
        # Executed: report the STRICT verdict for the ledger. The gate's restricted-
        # acceptance path keys off ``executed AND passed_gross`` directly (not this string);
        # the exact-dense-evidence path keys off ``executed AND passed`` (strict).
        if bool(certification.get("passed_gross", certification.get("passed", False))):
            return "passed_gross" if not bool(certification.get("passed", False)) else "passed"
        return "failed"
    reason = str(certification.get("reason", "not_executed"))
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


# --------------------------------------------------------------------------- #
# Metric helpers (field-standard; conventions carried).                         #
# --------------------------------------------------------------------------- #
def _gross_record_tv_budget(sampling_halfwidth: float) -> float:
    """The GROSS record/level TV gate budget: ``min(tau_gross_records + sampling_halfwidth,
    gross_ceiling)``. The Hoeffding ``sampling_halfwidth`` is added so a legitimately-sampled
    run (e.g. N=128) is not rejected for shot noise, but the total is CAPPED at
    ``_GROSS_RECORD_TV_CEILING`` so a tiny-N (N=3-5) finite-shot CI -- which can exceed 0.9
    per the Hoeffding form -- cannot inflate the budget past the incorrect-run TV floor
    (wrong-generator 0.5, no-op 1.0). Net: correct finite-step (<= ~0.14) + legit-sampling
    runs PASS; no-ops / wrong-branches ALWAYS FAIL regardless of N. Epistemic class (c)."""
    return float(min(_GROSS_RECORD_TV_GATE + float(sampling_halfwidth), _GROSS_RECORD_TV_CEILING))


def _total_variation_distance(p, q) -> float:
    """TV = 1/2 ||p-q||_1 over a shared support ordering (the standard statistical-distance
    convention; in [0,1])."""
    if len(p) != len(q):
        raise ValueError("TV distance requires equal-length probability vectors")
    return float(0.5 * sum(abs(float(a) - float(b)) for a, b in zip(p, q)))


def _total_variation_distance_dict(p: dict, q: dict) -> float:
    """TV = 1/2 sum_k |p_k - q_k| between two distributions keyed by outcome (the union of
    supports; missing keys contribute 0). The standard statistical-distance convention; in
    [0,1] for two probability distributions."""
    keys = set(p) | set(q)
    return float(0.5 * sum(abs(float(p.get(k, 0.0)) - float(q.get(k, 0.0))) for k in keys))


def _process_infidelity_and_choi_distance(
    carrier_superop, oracle_kraus, *, dim: int, oracle_superop=None
):
    """Process infidelity ``1 - F_e`` (Choi-state Uhlmann fidelity) + Choi trace distance
    between the CARRIER window superop and the ORACLE channel (Kraus stack OR superop; both
    column-stacking).

    numpy implementation that REPRODUCES the project's GPU convention EXACTLY
    (``joint_lindbladian._choi_state_from_kraus`` / ``_state_fidelity`` /
    ``composed_vs_joint_infidelity``, lines 494-573): column-stacking superop -> channel
    action; trace-normalised Choi states ``J/D``; Uhlmann fidelity via eigendecomposition;
    return ``max(0, 1 - F_pro)`` and ``1/2 ||J_c - J_o||_1`` (trace norm = sum|eigvals| of a
    Hermitian difference). Works on CPU (no CUDA dependency) so the red-test can run it.
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
    if oracle_superop is not None:
        oS = np.asarray(oracle_superop, dtype=np.complex128)
        J_oracle = _choi_state(lambda rho: _channel_action_superop(oS, rho))
    else:
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

    GPU-only (calls ``assemble_substep_channel`` + carrier torch helpers). The CPU red-test
    does NOT call this -- it injects ``_carrier_superop`` / ``_oracle_kraus`` directly.
    """
    import torch

    from ..carrier.joint_lindbladian import assemble_substep_channel
    from .axis1_carrier_program import axis1_carrier_program_manifest
    from .axis1_mcwf_mps_contract import (
        AXIS1_MCWF_MPS_CONTRACT_BACKEND_CONTRACT,
    )

    program = axis1_carrier_program_manifest(
        schedule, backend_contract=AXIS1_MCWF_MPS_CONTRACT_BACKEND_CONTRACT
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

    from .axis1_mcwf_mps_execution import (
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

    from .axis1_mcwf_mps_execution import (
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
# ADD 1: the dense joint-L LEVEL-POPULATION oracle (GPU production path).        #
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

    GPU-only (calls ``assemble_substep_channel``); the CPU red-test injects the oracle dict
    directly via ``_oracle_level_distribution``.
    """
    import numpy as np
    import torch

    from ..carrier.joint_lindbladian import assemble_substep_channel
    from .axis1_carrier_program import axis1_carrier_program_manifest
    from .axis1_mcwf_mps_contract import (
        AXIS1_MCWF_MPS_CONTRACT_BACKEND_CONTRACT,
    )
    from .axis1_mcwf_mps_execution import (
        _aggregating_measurement_boundary,
        _reset_basis,
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
        schedule, backend_contract=AXIS1_MCWF_MPS_CONTRACT_BACKEND_CONTRACT
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

    NUM_ZERO = 1e-12

    for substep in program["program"]["substeps"]:
        kind = str(substep.get("substep_kind"))
        if kind == "reset":
            # Projective reset to |0> per target (the carrier samples a level then resets to
            # the reset target vector |0>); as a channel this maps rho -> |0><0| on the site.
            new_branches = []
            for rho, prefix, w in branches:
                rho_new = rho
                for op in substep.get("operation_records", ()):
                    basis = _reset_basis(str(op.get("name", "")))
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
            # Aggregate ALL operation_records (multi-record terminal readout, mixed X/Z
            # basis) into ordered targets + per-target bases -- mirrors the carrier's
            # _aggregating_measurement_boundary. This oracle is INDEPENDENT of the sampler:
            # the H rotation below is rebuilt from scratch in numpy, never imported.
            boundary = _aggregating_measurement_boundary(substep)
            targets = [int(q) for q in boundary["measurement_targets"]]
            target_bases = [str(b).upper() for b in boundary["measurement_bases"]]
            # Post-measurement reset (the carrier's reset_after_measurement, Z-basis only):
            # after recording level l at the target, the conditioned site |l> -> |0> via the
            # carrier's reset operator |0><l| (see _apply_measurement_reset_if_requested_
            # multilevel + _reset_target_vector, Z basis target |0>).
            op_records = list(substep.get("operation_records", ()))
            reset_after = bool(
                len(op_records) == 1
                and op_records[0].get("reset_after_measurement", False)
            )
            reset_basis = str(op_records[0].get("basis", "Z")).upper() if op_records else "Z"
            if reset_after and reset_basis != "Z":
                raise _ChannelNotDenseCheckable(
                    "level_oracle_measurement_reset_supports_z_basis_only"
                )
            for target, target_basis in zip(targets, target_bases, strict=True):
                if target_basis not in {"X", "Z"}:
                    raise _ChannelNotDenseCheckable(
                        "level_oracle_measurement_supports_x_or_z_basis_only"
                    )
                dim_s = int(local_dims[target])
                if target_basis == "X":
                    # Independent numpy H = (1/sqrt2)[[1,1],[1,-1]] on the {|0>,|1>} block,
                    # identity on leaked levels: rotate the X-target into the Z eigenbasis
                    # before the Z-level projection below (no rotate-back; terminal readout).
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
                        p_level = float(np.trace(rho_cond).real)
                        if p_level <= NUM_ZERO:
                            continue
                        rho_norm = rho_cond / p_level
                        if reset_after:
                            # |0><l| on the conditioned (|l> at target) branch -> |0> at target.
                            Kr = np.zeros((dim_s, dim_s), dtype=np.complex128)
                            Kr[0, int(level)] = 1.0
                            Krf = lift_fn(Kr, (int(target),))
                            rho_norm = Krf @ rho_norm @ Krf.conj().T
                            tr = float(np.trace(rho_norm).real)
                            if tr > NUM_ZERO:
                                rho_norm = rho_norm / tr
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
