"""CoupledCycleNoiseProcess — evaluator-only source-coupled record process (slice 1, dense).

One shared memory-ful source trajectory ``z_t`` (Axis-2) is fanned out per QEC
cycle into coupled mechanism parameters (``source_coupling.Theta``), lowered
into per-round ``Axis1PrimitiveParams``, and emitted as real R-round
``{"det","obs"}`` records through the sealed dense Axis-1 record path
(``axis1_measurement_record_evidence_manifest`` with the injected
``params_for_substep`` callable). The process implements the
``audit.certify.types.ControlledNoiseProcess`` protocol surface (``sched`` /
``truth`` / ``emit`` / ``channels`` / ``emit_clifford_slice``) so its records
drop into ``certify_cells`` + the Anchor/Control ports unchanged.

Historical design evidence is retained in
``docs/twin_validation/coupled_cycle_teacher_design.md`` (Path A-corrected §2,
emit constraints §3, Theta homes §4, surface §5, red-team §6b). Runtime ownership
is entirely package-local: this module uses relative imports into
``error_coupling_simulator`` and has no inward dependency on the retained
repository-only ``qec_twin`` compatibility tree.

CONSTRAINT LEDGER (faithfulness protocol rule II — written BEFORE the
implementation below; each entry names its falsifying test in
``tests/test_coupled_cycle_teacher.py``):

C-1  Seal (red-team R5). ``emit`` refuses any schedule that does not carry the
     in-process compiler HMAC seal; schedules are constructed ONLY via
     ``compile_code_spec_to_substep_schedule`` (the seal key is
     process-lifetime ``secrets.token_bytes`` — analog_schedule.py:46 — so the
     process compiles its schedule in-process and a persisted/hand-built
     schedule can never claim "real circuit"). The dense record path itself
     also enforces the seal (axis1_channel_evidence.py:989); the emit-side
     assert is the process's own guarantee, not a duplicate dependency.
     Falsifier: ``test_emit_refuses_unsealed_schedule``.
C-2  Memory-ful shared source (red-team R3). The shared arm accepts only the
     declared memory-ful source classes (``OneOverFDriftSource`` — sum-of-RTN
     1/f with exact Lorentzian PSD — and ``RTNSource`` — autocorrelation
     ``exp(-2*gamma*lag)``); i.i.d.-like or permuted/baseline timelines are
     rejected as the shared arm. Falsifiers:
     ``test_shared_arm_rejects_non_memoryful_source``,
     ``test_shared_arm_rejects_baseline_timeline``.
C-3  Payload projection (red-team R4). ``emit`` returns EXACTLY
     ``{"det": (N, R*n_stab) uint8, "obs": (N,) uint8}`` — no manifest keys,
     no ``applied_steps`` (which leak num_kraus / ideal-control names / dt —
     axis1_record_evidence.py:535-571), no truth. Falsifier:
     ``test_emit_payload_surface``.
C-4  Round derivation (red-team R1). The substep->round map is derived from
     ``tick_index`` (the compiler emits ONE ``builder.tick()`` per round —
     compiler.py:66-69) and CROSS-VALIDATED at construction against three
     independent witnesses: (i) measurement-key prefixes ``round{r}:`` must
     equal the tick-derived round (record_layout.py:195-196), (ii) terminal
     data keys ``final:q{i}:{basis}`` (record_layout.py:207-208) must sit at
     ``tick_index == rounds`` (terminal substeps take the LAST round's params —
     declared clamp policy), (iii) barrier count must equal ``rounds``. Any
     disagreement raises; there is NO uniform-params fallback; the dead
     ``AnalogSubstepIR.round_index`` field (hardcoded ``None``,
     analog_schedule.py:871/899) is never read. Falsifiers:
     ``test_round_map_two_round_schedule`` (terminal off-by-one),
     ``test_round_map_tampered_keys_raise``,
     ``test_params_differ_across_rounds`` (positive control).
C-5  Per-round param fan-out mapping. Per-cycle ``CoupledMechanismParams``
     map 1:1 into ``Axis1PrimitiveParams``: ``zz_zeta_radns ->
     zeta_rad_per_ns`` (both angular rad/ns; the ZZ primitive lowers
     ``H = zeta * n(x)n`` — axis1_primitives.py:271-273; a negative zeta fails
     loud at ``Axis1PrimitiveParams`` construction, never silently abs()-ed)
     and ``gamma_phi_per_ns -> gamma_phi_per_ns`` (both 1/ns; the T2 collapse
     lowers ``c = sqrt(2*gamma_phi) * n`` so the qubit coherence decays as
     ``exp(-gamma_phi * t)``). Every other field (``gamma_1_per_ns``,
     ``gamma_up``, ``gamma_readout_phi``, drive, fSim) is held at the schedule
     baseline (slice-1 scope, class (c), see S-3). Falsifier: the independent
     ground-truth response test ``test_x0_delta_rate_tracks_gamma_phi`` (a
     wrong field mapping breaks its direction/magnitude band).
C-6  Distribution gate. ``emit`` refuses to sample when the exact manifest
     reports ``passed != True`` (total-probability residual > 1e-8 or
     incomplete positive-duration coverage) — never a silent sample from a
     broken enumeration. Runtime guard (fail-loud); no committed fixture can
     currently produce a failed manifest, declared as an untested guard.
C-7  Isolation (G7). ``truth`` is evaluator-only, reachable only via the
     ``.truth`` property (returned separately in ``CertReport.truth``, never
     included in emitted records); it contains no ``det``/``obs`` arrays and the emit payload
     contains no truth keys. Falsifier: ``test_truth_isolation``.
C-8  Reproducibility. Same ``(regime, m, N, seed)`` => byte-identical
     ``{det,obs}``. Per-trajectory seeds are stable sha256 derivations of
     ``(seed, trajectory, purpose)`` — never Python ``hash()``. Falsifier:
     ``test_emit_reproducible``.
C-9  Ablation arms. ``markovian_baseline()`` preserves each one-field
     marginal (per-field permutations of the SAME trajectory,
     ``independent_baseline_trajectory_to_params``) while destroying the
     temporal ORDER (hence the cross-cycle 1/f autocorrelation) and the
     same-cycle cross-mechanism alignment; ``off_source()`` collapses the
     fan-out to the constant Theta(0) point. NOTE (corrected 2026-07-03 with
     prereg §5 re-registration): the per-field permutation is EXCHANGEABLE,
     not independent — at finite R the markovian arm RETAINS most of the
     shared arm's shot-pooled lag-1 record covariance (the permutation-
     invariant trajectory-mean-instrument common-mode plus a small
     -Var/(R-1) exchangeable term; ~0.73 of the shared lag-1 covariance at
     R=12). The two arms differ only in the second-order cross-cycle MEMORY
     residue, which is sub-floor on records at feasible N (see
     ``docs/twin_validation/g6_null_model_rederivation_2026-07-03.md``).
     Falsifiers: ``test_markovian_baseline_marginals_and_decorrelation``,
     ``test_off_source_constant_params``.
C-10 Independent ground truth (faithfulness rule I). Emitted record
     statistics are checked against closed forms derived OUTSIDE this module
     and outside the dense emitter's probability tables: (a) the Z-check
     chain of the compiled fixture is Z-diagonal end-to-end, so its per-round
     record rate is pure instrument algebra
     ``p = p_rs + p_ro - 2*p_rs*p_ro`` (+ a bounded gamma_1 correction) and
     the ``delta:z1`` detector fires at ``2p(1-p)``; (b) the X-check
     round-delta rate must rise with gamma_phi with magnitude
     ``0.5*(exp(-gph_A*tau) - exp(-gph_B*tau))`` inside the declared
     ``tau_eff`` bracket. Falsifiers: ``test_z1_rates_match_closed_form``,
     ``test_x0_delta_rate_tracks_gamma_phi`` (derivations in their
     docstrings).
C-11 Batching (red-team R6). ``shots_per_trajectory > 1`` is a declared perf
     knob (default 1 = one trajectory per shot); the value and the cluster
     structure (rows within one cluster share one trajectory's exact
     conditional distribution; clusters are independent) are recorded in
     ``truth``. Falsifier: ``test_batched_emit_declares_clusters``.
C-12 Logical prep grounding. The compiled fixture prepares ``|0...0>`` with a
     Z-basis logical readout of data qubit 2 (``logical_z2``) — logical
     ``m=0`` ONLY; ``emit(m=1)`` raises ``NotImplementedError`` (the compiler
     emits no logical-X frame), never silently emits wrong-prep records.
     Falsifier: ``test_m1_raises``.

BOUNDED SIMPLIFICATIONS (faithfulness protocol rule III — all class (c)
unless noted, all recorded in ``truth``):

S-1  Trajectory-mean readout/reset instrument. ``readout_flip_p`` /
     ``reset_flip_p`` enter as the per-trajectory MEAN
     (``Axis1ReadoutResetInstrumentSpec``), suppressing their per-round
     variation (single-slot instrument limitation; design §4 per-round
     caveat, user-resolved 2026-06-30). Bound: the suppressed per-round
     logit-modulation at |x|<=3 is |dp| <= p*(exp(0.40*3)-1) ~ 2.3*p per
     round about a p ~ 1e-2 base; the per-trajectory MEAN is preserved
     exactly, so NO within-shot cross-cycle memory is added or removed by this
     simplification. CORRECTION (2026-07-03): the trajectory mean itself VARIES
     shot-to-shot (each shot draws its own trajectory), so pooling over shots
     the instrument injects a permutation-INVARIANT common-mode covariance
     (~8.7e-5 per check, at ALL lags) into the record statistics — identical
     in the shared and markovian arms (it depends only on the trajectory mean),
     hence it cancels in the shared-minus-markovian difference but is NOT
     ~0 in either arm's raw statistic. This is why the record-level MA(1) floor
     (off-arm Spitz p_ij(lag1) = p_ro + p_rs - 2 p_ro p_rs ~ 0.0149, not 0) and
     the common-mode dominate the raw lag-1/lag-2 z-scores; see
     ``docs/twin_validation/g6_null_model_rederivation_2026-07-03.md`` and the
     re-registered prereg §5. Per-round instruments are a later slice.
S-2  ``channels()`` at the mean-source point. The reported per-substep CPTP
     field is assembled at Theta(0) (z = E[z] = 0 for the symmetric RTN-sum
     sources), NOT the mean of per-shot channels. Jensen gap: for +/-1
     fluctuator sums, E[exp(s*x)] = cosh(s) per fluctuator, e.g. ~6.2%
     understatement of the trajectory-mean gamma_phi at the default
     sensitivity 0.35 and 1-sigma normalization. ``channels()`` is NOT in the
     emit path; per-shot fields are regenerable from truth seeds.
S-3  gamma_1 (and gamma_up, gamma_readout_phi, drive, fSim) are NOT
     source-modulated in slice 1 — held at the schedule baseline
     (``_axis1_primitive_params_for_schedule``); the deferred Theta fields
     (``detuning_radns``, ``drive_omega_radns``, ``spillover_cx``,
     ``cz_depol_p``) are recorded in truth as DEFERRED and never emitted
     (adjudicated slice-1 scope).
S-4  Record-dead zeta (faithful property, exact evidence). Under realistic
     1/f draws the per-cycle static-ZZ variation leaves ~no record imprint
     (G0-v1 zeta-only record TV ~ 4.3e-11 vs gamma_phi-carried TV ~ 5.8e-4;
     ``outputs/twin_validation/g0_zeta_gammaphi_effectsize.py``, 2026-06-30,
     liveness positive control PASSED). zeta is nonetheless carried
     faithfully per-round into the channel (the schedule declares the
     superposition-bearing X-check static-ZZ edge (0,3) WITHOUT a per-edge
     calibration, so the per-round ``params.zeta_rad_per_ns`` is what lowers —
     axis1_channel_evidence.py:806-814). The record-level Axis-2 carrier is
     gamma_phi.
S-5  Exponential inner enumeration. The dense path enumerates
     2^(#measurement keys) branches (x instrument branching), so R is small;
     R* and N* are G0-v2 design constants (Builder 3's lane) — ``rounds`` is
     a constructor argument, never hardcoded here.
S-6  Small table cache. Identical (per-round params, instrument) keys reuse
     the exact record tables (pure memoization of a deterministic
     enumeration; exactness unchanged). Bounded to the 4 most recent keys.
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import math
import re
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from ..mechanisms.axis1_primitives import Axis1PrimitiveParams
from ..numerics import NUMERICAL_ZERO
from ..source.coupling import (
    CoupledMechanismParams,
    SourceCouplingConfig,
    default_source_coupling_config,
    independent_baseline_trajectory_to_params,
    source_to_params,
    trajectory_to_params,
)
from ..source.process import (
    OneOverFDriftSource,
    RTNSource,
    SourceProcess,
    SourceTimeline,
)
from ..frontend.analog_schedule import (
    SubstepSchedule,
    compile_code_spec_to_substep_schedule,
    has_valid_compiler_schedule_seal,
    require_compiler_schedule_seal,
)
from ..frontend.axis1_channel_evidence import (
    _assemble_selection_joint_channel,
    _axis1_primitive_params_for_schedule,
    _axis1_static_zz_calibrations_for_schedule,
    _nominal_positive_dt,
)
from ..frontend.axis1_codespec_runner import (
    build_axis1_codespec_4q_frontend_spec,
    build_axis1_codespec_frontend_spec,
)
from ..frontend.axis1_context import Axis1LocalLindbladContextSpec
from ..frontend.axis1_record_evidence import (
    Axis1ReadoutResetInstrumentSpec,
    axis1_measurement_record_evidence_manifest,
)
from ..frontend.axis1_selection import (
    axis1_selection_layers_in_schedule_order,
    build_axis1_schedule_selection_plan,
)
from ..frontend.code_spec import (
    Axis1StaticZZDeviceSpec,
    CodeQubit,
    CodeSpec,
    LogicalObservableSpec,
    PauliTerm,
    StabilizerCheck,
)
from ..frontend.source_sidecar import (
    SourceTimelineBinding,
    build_source_timeline_binding_manifest,
)

COUPLED_TEACHER_SCHEMA = "qec_twin.mechanisms.CoupledCycleNoiseProcess.v1"
#: Representability-ledger class string (declared; mirrored in
#: ``src/qec_twin/simulator/README.md``): sampled Axis-1 joint-L records under a
#: shared-source per-round param fan-out, truth evaluator-only.
COUPLED_TEACHER_REPRESENTABILITY = (
    "axis1_jointL_source_coupled_record_samples_evaluator_truth"
)

#: The declared memory-ful shared-arm source classes (C-2 / red-team R3).
#: OneOverFDriftSource = slice-1 source (sum-of-RTN 1/f, exact Lorentzian PSD);
#: RTNSource = the contrast control (single Lorentzian, autocorr e^{-2 gamma lag}).
#: PhaseBurstSource / TemporalStormSPPSource / arbitrary SourceProcess impls are
#: NOT accepted as the shared arm this slice (their payload shapes and memory
#: classes are not certified for this process).
MEMORYFUL_SHARED_SOURCES = (OneOverFDriftSource, RTNSource)

#: The X-check data<->ancilla pair of the 5q fixture — the only
#: superposition-bearing edge, where static-ZZ is observable (grounded by the
#: G0-v1 empirical wiring section; see S-4). Declared WITHOUT a per-edge
#: calibration so the per-round ``params.zeta_rad_per_ns`` lowers on it.
DEFAULT_STATIC_ZZ_EDGE = (0, 3)

_ROUND_KEY_RE = re.compile(r"^round(\d+):")
_FINAL_KEY_RE = re.compile(r"^final:q(\d+):[XYZ]$")
_TABLE_CACHE_MAX = 4
#: F4 (2026-07-03): widened from 1 to 32 so C1's per-round-spread fraction has real power (a single
#: frozen 1/f trajectory, P~2e-4, no longer forces frac_spread=0 -> false FAIL). Records 32
#: trajectories' per-cycle params in truth (evaluator-only); the instrument/source-binding sample
#: stays at the first trajectory only.
_TRUTH_PARAMS_SAMPLE_TRAJECTORIES = 32
_TRUTH_SEED_SAMPLE = 8


# --------------------------------------------------------------------------- #
# round derivation (C-4)                                                       #
# --------------------------------------------------------------------------- #
def derive_round_map_for_substep_schedule(
    schedule: SubstepSchedule,
    *,
    rounds: int,
) -> dict[str, tuple[int, bool]]:
    """Return the validated ``substep_id -> (round_index, is_terminal)`` map.

    Round index is DERIVED from ``tick_index`` (one compiler tick per round)
    and cross-validated against the measurement-key prefixes and the barrier
    count; the dead ``AnalogSubstepIR.round_index`` field is never read.
    Terminal substeps (``tick_index == rounds``: the final data readout and
    anything after the last tick) are clamped to the LAST round's params —
    the declared class-(c) terminal policy: the source ``z_t`` is
    piecewise-constant per cycle and the last value extends through terminal
    readout. Any key/tick disagreement raises (no uniform-params fallback —
    red-team R1).
    """

    n_rounds = int(rounds)
    if n_rounds < 1:
        raise ValueError(f"rounds must be >= 1, got {rounds!r}")
    round_map: dict[str, tuple[int, bool]] = {}
    barrier_ticks: list[int] = []
    seen_rounds: set[int] = set()
    seen_terminal_keys = False
    for substep in schedule.substeps:
        tick = int(substep.tick_index)
        if substep.kind == "barrier":
            barrier_ticks.append(tick)
        if tick < n_rounds:
            assignment = (tick, False)
        elif tick == n_rounds:
            assignment = (n_rounds - 1, True)
        else:
            raise ValueError(
                f"substep {substep.substep_id!r} has tick_index={tick} beyond the "
                f"terminal block of a {n_rounds}-round schedule; round derivation "
                "cannot be validated"
            )
        for key in substep.measurement_keys:
            round_match = _ROUND_KEY_RE.match(key)
            if round_match is not None:
                parsed = int(round_match.group(1))
                if parsed >= n_rounds:
                    raise ValueError(
                        f"measurement key {key!r} names round {parsed} outside a "
                        f"{n_rounds}-round schedule"
                    )
                if parsed != tick:
                    raise ValueError(
                        f"round derivation mismatch on substep {substep.substep_id!r}: "
                        f"key {key!r} names round {parsed} but tick_index={tick} "
                        "(red-team R1: refusing, never falling back to uniform params)"
                    )
                seen_rounds.add(parsed)
            elif _FINAL_KEY_RE.match(key) is not None:
                if tick != n_rounds:
                    raise ValueError(
                        f"terminal data key {key!r} sits at tick_index={tick}, "
                        f"expected the terminal block tick_index={n_rounds}"
                    )
                seen_terminal_keys = True
            else:
                raise ValueError(
                    f"unrecognized measurement key {key!r} on substep "
                    f"{substep.substep_id!r}; round derivation cannot be validated"
                )
        round_map[substep.substep_id] = assignment
    if sorted(barrier_ticks) != list(range(n_rounds)):
        raise ValueError(
            f"barrier witness mismatch: expected one barrier per round "
            f"(ticks {list(range(n_rounds))}), got ticks {sorted(barrier_ticks)}"
        )
    if seen_rounds != set(range(n_rounds)):
        raise ValueError(
            f"measurement keys cover rounds {sorted(seen_rounds)}, expected all of "
            f"{list(range(n_rounds))}; rounds argument and schedule disagree"
        )
    if not seen_terminal_keys:
        raise ValueError("no terminal 'final:q{i}:{basis}' measurement keys found")
    return round_map


def params_for_substep_from_round_map(
    round_map: Mapping[str, tuple[int, bool]],
    per_round_params: Sequence[Axis1PrimitiveParams],
) -> Callable[[Any], Axis1PrimitiveParams]:
    """Build the injected ``params_for_substep`` callable (pinned interface).

    The callable receives the full ``AnalogSubstepIR`` and resolves that
    substep's round through the construction-validated map; an unknown
    substep id raises (no fallback — red-team R1).
    """

    resolved = {str(k): (int(v[0]), bool(v[1])) for k, v in round_map.items()}
    per_round = tuple(per_round_params)

    def _params_for_substep(substep: Any) -> Axis1PrimitiveParams:
        substep_id = str(getattr(substep, "substep_id"))
        if substep_id not in resolved:
            raise ValueError(
                f"substep {substep_id!r} is not in the validated round map; "
                "refusing to guess its round (red-team R1)"
            )
        round_index, _terminal = resolved[substep_id]
        return per_round[round_index]

    return _params_for_substep


# --------------------------------------------------------------------------- #
# fan-out lowering helpers (C-5, S-1)                                           #
# --------------------------------------------------------------------------- #
def per_round_axis1_params(
    baseline: Axis1PrimitiveParams,
    coupled: CoupledMechanismParams,
) -> Axis1PrimitiveParams:
    """Lower one cycle's ``CoupledMechanismParams`` onto the schedule baseline.

    Unit-exact 1:1 mappings (C-5): ``zz_zeta_radns -> zeta_rad_per_ns`` (both
    angular rad/ns; ``H_ZZ = zeta * n(x)n``) and ``gamma_phi_per_ns ->
    gamma_phi_per_ns`` (both 1/ns; ``c_T2 = sqrt(2*gamma_phi) * n``, coherence
    decay ``exp(-gamma_phi t)``). All other fields stay at the baseline
    (S-3). A negative zeta fails loud in ``Axis1PrimitiveParams.__post_init__``.
    """

    return dataclasses.replace(
        baseline,
        zeta_rad_per_ns=float(coupled.zz_zeta_radns),
        gamma_phi_per_ns=float(coupled.gamma_phi_per_ns),
    )


def trajectory_mean_instrument(
    params_cycles: Sequence[CoupledMechanismParams],
) -> Axis1ReadoutResetInstrumentSpec:
    """Trajectory-mean readout/reset instrument (S-1, class (c), declared).

    ``readout_flip_p`` enters symmetrically (``p0->1 == p1->0`` — the Theta
    fan-out carries one symmetric flip probability); pair-flip crosstalk is
    not a Theta field this slice and stays 0.
    """

    if not params_cycles:
        raise ValueError("trajectory_mean_instrument requires at least one cycle")
    readout = float(np.mean([float(p.readout_flip_p) for p in params_cycles]))
    reset = float(np.mean([float(p.reset_flip_p) for p in params_cycles]))
    return Axis1ReadoutResetInstrumentSpec(
        readout_p0_to_1=readout,
        readout_p1_to_0=readout,
        readout_pair_flip_probability=0.0,
        reset_flip_probability=reset,
        source="coupled_cycle_teacher_trajectory_mean_v1",
        epistemic_class="c",
    )


def _wrap_coupled_code_spec(base: CodeSpec, cfg: SourceCouplingConfig) -> CodeSpec:
    """Add the coupled-fixture metadata to a frontend CodeSpec (shared by the 5q + 4q variants).

    (a) the superposition-bearing static-ZZ edge (0,3) WITHOUT a per-edge calibration (so the
    per-round ``zeta_rad_per_ns`` from the injected callable is what lowers on it — S-4) and (b) an
    ``Axis1LocalLindbladContextSpec`` baseline pinned to the Theta(0) fan-out point (zeta and
    gamma_phi at z=0). The context pin makes the no-callable schedule-global path physically
    identical to the off-source arm — the construction-independence control
    ``test_off_source_matches_plain_manifest`` relies on this identity.
    """

    theta0 = source_to_params(0.0, cfg)
    metadata = dict(base.metadata)
    metadata.update(
        Axis1StaticZZDeviceSpec(
            edges=(DEFAULT_STATIC_ZZ_EDGE,),
            num_qubits=base.num_qubits,
        ).to_metadata()
    )
    metadata.update(
        Axis1LocalLindbladContextSpec(
            zeta_rad_per_ns=float(theta0.zz_zeta_radns),
            gamma_phi_per_ns=float(theta0.gamma_phi_per_ns),
        ).to_metadata()
    )
    return dataclasses.replace(base, metadata=metadata)


def default_coupled_code_spec(
    rounds: int,
    config: SourceCouplingConfig | None = None,
) -> CodeSpec:
    """The slice-1 coupled fixture: the 5q mixed-basis CodeSpec (x0 + z1) + Theta(0) baseline.

    3 data + 2 ancilla; checks x0 (X on data 0) + z1 (Z on data 1); logical_z2 (Z on data 2);
    n_stab = 2, measured bits M(R) = 2R + 3. See :func:`_wrap_coupled_code_spec` for the added
    static-ZZ edge + Theta(0) context.
    """

    cfg = config or default_source_coupling_config()
    return _wrap_coupled_code_spec(build_axis1_codespec_frontend_spec(rounds=int(rounds)), cfg)


def default_coupled_code_spec_4q(
    rounds: int,
    config: SourceCouplingConfig | None = None,
) -> CodeSpec:
    """The registered 4q coupled fixture (prereg §1.1): drop z1 -> single X-check x0.

    3 data + 1 ancilla; check x0 only (same static-ZZ edge (0,3)); logical_z2 (Z on data 2);
    data qubit 1 in no check/observable -> no final measurement; n_stab = 1, measured bits
    M(R) = R + 2. Reachable by name so a JSON ``teacher_kwargs = {"rounds": R, "fixture": "4q"}``
    can construct it through the gate config seam (F2). Same Theta(0) baseline wrapping as the 5q.
    """

    cfg = config or default_source_coupling_config()
    return _wrap_coupled_code_spec(build_axis1_codespec_4q_frontend_spec(rounds=int(rounds)), cfg)


def default_coupled_code_spec_d3_repz(
    rounds: int,
    config: SourceCouplingConfig | None = None,
) -> CodeSpec:
    """The P0 genuine-decode fixture: a distance-3 bit-flip repetition code.

    3 data (0,1,2) + 2 ancilla (3: z01, 4: z12); weight-2 Z checks Z0Z1 / Z1Z2;
    logical_z2 (Z on data 2, the chain end). M(R) = 2R + 3 measured bits — the
    SAME enumeration cost as the 5q fixture (S-5 unchanged). Unlike the 5q
    fixture (whose logical_z2 is structurally disconnected from both weight-1
    checks), the logical-flipping fault class here fires a detector, so an
    MWPM decode of the emitted record is non-vacuous.

    DECLARED slice-1 fault-class map (P0 interop scope; the C-10a Z-diagonal
    argument applies to every chain — reviewed 2026-07-06):
    - gamma_phi / zeta are record-DEAD in this all-Z geometry; gamma_1 is
      inert on the |0...0> prep; gamma_up is held at the schedule baseline 0.
      There is NO data-X fault class in slice 1 — the record's error content
      is entirely the readout/reset instrument.
    - Per-round ancilla flip p = p_rs + p_ro - 2 p_rs p_ro; interior deltas
      fire at ~2p(1-p). A ROUND-0 ancilla flip fires ONLY delta:<check>:round1
      (the layout has no round-0 anchor detector) and does NOT flip the
      observable — so delta-column boundary classes carry NO logical
      attachment under slice-1 noise.
    - The ONLY observable-flipping fault class is the final:q2:Z data-readout
      flip, which fires the final:z12 closure -> the declared L0 rule for this
      fixture+noise is exactly {final:z12}. (Geometrically an in-round X on q2
      WOULD populate delta:z12 boundaries with L0, but that class has
      probability 0 in slice 1 — the L0 rule is a reduction of the RECORD's
      fault mix, not of the code geometry.)
    This fixture exercises the interop/decode path on instrument noise — it is
    NOT a coupling-visibility arm; the coupling-visible demo geometry is P3's
    job. Same Theta(0) baseline wrapping as the other fixtures (the static-ZZ
    edge (0,3) is inert here — declared).
    """

    cfg = config or default_source_coupling_config()
    spec = CodeSpec(
        name="d3_repz_coupled_fixture",
        num_qubits=5,
        data_qubits=(
            CodeQubit(0, "data", (0.0,)),
            CodeQubit(1, "data", (2.0,)),
            CodeQubit(2, "data", (4.0,)),
        ),
        ancilla_qubits=(
            CodeQubit(3, "ancilla", (1.0,)),
            CodeQubit(4, "ancilla", (3.0,)),
        ),
        checks=(
            StabilizerCheck(
                "z01", 3, (PauliTerm(0, "Z"), PauliTerm(1, "Z")), coords=(1.0,)
            ),
            StabilizerCheck(
                "z12", 4, (PauliTerm(1, "Z"), PauliTerm(2, "Z")), coords=(3.0,)
            ),
        ),
        logical_observables=(
            LogicalObservableSpec("logical_z2", (PauliTerm(2, "Z"),)),
        ),
        rounds=int(rounds),
    )
    return _wrap_coupled_code_spec(spec, cfg)


#: JSON-reachable fixture selector -> default coupled CodeSpec builder (F2). ``code_spec_builder``
#: (a callable) still overrides this when provided; ``fixture`` picks the default when it is None.
_COUPLED_FIXTURE_BUILDERS: dict[str, Callable[[int, SourceCouplingConfig | None], CodeSpec]] = {
    "5q": default_coupled_code_spec,
    "4q": default_coupled_code_spec_4q,
    "d3_repz": default_coupled_code_spec_d3_repz,
}


def _derived_seed(base_seed: int, trajectory: int, purpose: str) -> int:
    """Stable per-(seed, trajectory, purpose) derivation (C-8; never ``hash()``)."""

    payload = (
        f"{COUPLED_TEACHER_SCHEMA}:{int(base_seed)}:{int(trajectory)}:{purpose}"
    ).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "big") % (2**63 - 1)


# --------------------------------------------------------------------------- #
# the controlled process                                                        #
# --------------------------------------------------------------------------- #
class CoupledCycleNoiseProcess:
    """Evaluator-only ``ControlledNoiseProcess`` carrying Axis-1 x Axis-2 coupling.

    Outer Monte-Carlo over memory-ful source trajectories (one per shot by
    default), inner EXACT conditional record distribution
    ``P(det, obs | z_traj)`` from the dense sealed Axis-1 record path with the
    per-round ``params_for_substep`` callable. Only ``rounds`` is required —
    the R*/N* design constants belong to the G0-v2 gate (S-5).

    ``coupling_arm``: ``"shared"`` (the source-coupled process), ``"independent"`` (the G6
    matched-marginal negative control, built via :meth:`markovian_baseline`),
    ``"off"`` (the amplitude-0 collapse arm, built via :meth:`off_source`).
    """

    def __init__(
        self,
        rounds: int,
        *,
        source: SourceProcess | None = None,
        config: SourceCouplingConfig | None = None,
        shots_per_trajectory: int = 1,
        device: str = "cuda",
        code_spec_builder: Callable[[int], CodeSpec] | None = None,
        fixture: str = "5q",
        coupling_arm: str = "shared",
    ) -> None:
        self._rounds = int(rounds)
        if self._rounds < 2:
            raise ValueError(
                "CoupledCycleNoiseProcess requires rounds >= 2: cross-cycle source "
                f"memory needs at least two cycles, got rounds={rounds!r}"
            )
        if coupling_arm not in {"shared", "independent", "off"}:
            raise ValueError(f"unknown coupling_arm {coupling_arm!r}")
        self._arm = str(coupling_arm)
        self._config = config or default_source_coupling_config()
        self._source = source if source is not None else OneOverFDriftSource()
        if not isinstance(self._source, MEMORYFUL_SHARED_SOURCES):
            raise ValueError(
                "CoupledCycleNoiseProcess accepts only the declared memory-ful source "
                "classes (OneOverFDriftSource, RTNSource) — an i.i.d./uncertified "
                f"source as the shared arm is red-team R3; got "
                f"{type(self._source).__name__}"
            )
        self._shots_per_trajectory = int(shots_per_trajectory)
        if self._shots_per_trajectory < 1:
            raise ValueError(
                f"shots_per_trajectory must be >= 1, got {shots_per_trajectory!r}"
            )
        self._device = str(device)
        if not self._device.startswith("cuda"):
            raise ValueError(
                "CoupledCycleNoiseProcess is GPU-only (repo device policy); pass "
                f"device='cuda', got {device!r}"
            )
        self._fixture = str(fixture)
        if self._fixture not in _COUPLED_FIXTURE_BUILDERS:
            raise ValueError(
                f"unknown fixture {fixture!r}; expected one of "
                f"{sorted(_COUPLED_FIXTURE_BUILDERS)} (or pass an explicit code_spec_builder)"
            )
        self._code_spec_builder = code_spec_builder
        if code_spec_builder is None:
            # F2: JSON-reachable fixture selector -> default coupled CodeSpec builder.
            self._spec = _COUPLED_FIXTURE_BUILDERS[self._fixture](self._rounds, self._config)
        else:
            self._spec = code_spec_builder(self._rounds)
        if int(self._spec.rounds) != self._rounds:
            raise ValueError(
                f"code spec declares rounds={self._spec.rounds}, teacher was "
                f"constructed with rounds={self._rounds}"
            )
        # C-1: in-process compiler path only (the seal key is process-lifetime).
        self._sched = compile_code_spec_to_substep_schedule(self._spec)
        require_compiler_schedule_seal(self._sched)
        if self._sched.source_kind != "code_spec_compiler":
            raise ValueError(
                f"expected a compiler schedule, got source_kind={self._sched.source_kind!r}"
            )
        # C-4: derived + three-witness-validated round map.
        self._round_map = derive_round_map_for_substep_schedule(
            self._sched, rounds=self._rounds
        )
        self._n_stab = len(self._spec.checks)
        layout = self._sched.record_layout_ref
        self._detector_names = tuple(
            str(d["name"]) for d in layout.get("detectors", ())
        )
        self._observable_names = tuple(
            str(o["name"]) for o in layout.get("observables", ())
        )
        self._measurement_keys = tuple(
            str(k) for k in layout.get("measurement_keys", ())
        )
        if len(self._detector_names) != self._rounds * self._n_stab:
            raise ValueError(
                f"detector count {len(self._detector_names)} != rounds*n_stab = "
                f"{self._rounds * self._n_stab}; the (N, R*n_stab) det surface "
                "cannot be honored"
            )
        if len(self._observable_names) != 1:
            raise ValueError(
                "the (N,) obs surface requires exactly one logical observable, "
                f"got {list(self._observable_names)}"
            )
        # Baseline params via the SAME resolution the dense emitter uses for its
        # default path (no drift between process baseline and emitter default).
        self._baseline_params = _axis1_primitive_params_for_schedule(self._sched)
        self._table_cache: dict[tuple, tuple] = {}
        self._last_emit: dict[str, Any] | None = None

    # ------------------------------------------------------------------ #
    # ControlledNoiseProcess protocol surface                                   #
    # ------------------------------------------------------------------ #
    @property
    def sched(self) -> SubstepSchedule:
        """The sealed compiler-generated R-round substep schedule."""

        return self._sched

    @property
    def truth(self) -> dict:
        """Evaluator-only ground truth (C-7). Never part of the emit payload."""

        source_manifest = dataclasses.asdict(self._source)
        source_manifest["class"] = type(self._source).__name__
        truth: dict[str, Any] = {
            "schema": COUPLED_TEACHER_SCHEMA,
            "visibility": "evaluator_only",
            "representability": COUPLED_TEACHER_REPRESENTABILITY,
            "coupling_arm": self._arm,
            "fixture": self._fixture,
            "source": source_manifest,
            "source_memoryful_whitelist": [
                cls.__name__ for cls in MEMORYFUL_SHARED_SOURCES
            ],
            "config": self._config.to_manifest(),
            "rounds": self._rounds,
            "n_stab": self._n_stab,
            "num_qubits": int(self._sched.num_qubits),
            "detector_names": list(self._detector_names),
            "observable_names": list(self._observable_names),
            "det_column_semantics": (
                "columns follow record_layout declaration order: rounds 1..R-1 "
                "round-delta detectors (n_stab per round) then n_stab "
                "final-closure detectors; reshaping (N, R, n_stab) is round-major"
            ),
            "schedule": {
                "source_kind": self._sched.source_kind,
                "source_hash": self._sched.source_hash,
                "sealed": has_valid_compiler_schedule_seal(self._sched),
                "static_zz_couplings": [
                    list(edge) for edge in self._sched.static_zz_couplings
                ],
            },
            "baseline_axis1_params": self._baseline_params.to_manifest(),
            "per_round_modulated_fields": ["zeta_rad_per_ns", "gamma_phi_per_ns"],
            "held_at_baseline_fields": [
                "gamma_1_per_ns",
                "gamma_up_per_ns",
                "gamma_readout_phi_per_ns",
                "drive_area_rad",
                "drive_omega_rad_per_ns",
                "fsim_delta_theta_rad",
                "fsim_delta_phi_rad",
            ],
            "deferred_theta_fields": {
                "detuning_radns": "c",
                "drive_omega_radns": "c",
                "spillover_cx": "c",
                "cz_depol_p": "c",
            },
            "instrument_policy": {
                "kind": "trajectory_mean_readout_reset",
                "epistemic_class": "c",
                "readout_symmetric": True,
                "pair_flip_probability": 0.0,
                "note": (
                    "readout/reset held at the per-trajectory mean of the Theta "
                    "fan-out (single-slot instrument; S-1); per-round instruments "
                    "are a later slice"
                ),
            },
            "channels_policy": {
                "kind": "mean_field_theta_zero",
                "epistemic_class": "c",
                "note": (
                    "channels() is assembled at the Theta(0) point; per-shot "
                    "fields are regenerable from the seed derivation below (S-2)"
                ),
            },
            "record_dead_zeta_note": {
                "statement": (
                    "per-cycle static-ZZ variation is record-dead under realistic "
                    "1/f draws (faithful property, not a bug); the record-level "
                    "Axis-2 carrier is gamma_phi"
                ),
                "evidence": "outputs/twin_validation/g0_zeta_gammaphi_effectsize.py",
                "g0_v1_zeta_only_record_tv": 4.3e-11,
                "g0_v1_joint_record_tv": 5.77e-4,
            },
            "shots_per_trajectory": self._shots_per_trajectory,
            "seed_derivation": {
                "scheme": (
                    "sha256('"
                    + COUPLED_TEACHER_SCHEMA
                    + ":{seed}:{trajectory}:{purpose}')[:8] as big-endian int "
                    "mod 2**63-1"
                ),
                "purposes": ["source", "independent_permutation", "sample"],
            },
            "epistemic_classes": {
                "record_sampling_from_exact_distribution": "a",
                "round_derivation_and_validation": "a",
                "theta_fan_out_constants": "c",
                "instrument_probability_values": "c",
                "trajectory_mean_instrument_policy": "c",
                "mean_field_channels": "c",
                "terminal_round_clamp_policy": "c",
                "table_cache_memoization": "a",
            },
            # F7: a SNAPSHOT (deep copy), never a live reference to the mutable bookkeeping dict —
            # an evaluator holding truth must not see it mutate on the next emit, nor be able to
            # mutate the process's internal state through it.
            "last_emit": copy.deepcopy(self._last_emit),
        }
        return truth

    def emit(self, regime: Any, *, m: int, N: int, seed: int) -> dict[str, np.ndarray]:
        """Emit ``N`` records — the ``{"det","obs"}`` surface and NOTHING else.

        Outer MC: trajectory ``j`` covers shots ``[j*spt, ...)``; its source
        timeline, Theta fan-out, per-round params, trajectory-mean instrument
        and ONE exact manifest call produce the conditional record tables the
        shots are multinomial-sampled from. Validation (seal, regime, m) runs
        before any device work.
        """

        # C-1 (emit-side seal assert, red-team R5).
        require_compiler_schedule_seal(self._sched)
        self._validate_regime(regime)
        if int(m) != 0:
            # C-12: the compiled fixture prepares |0...0> — logical m=0 only.
            raise NotImplementedError(
                "CoupledCycleNoiseProcess slice-1 supports logical m=0 only: the "
                "compiled fixture prepares |0...0> with a Z-basis logical "
                "readout and the compiler emits no logical-X frame; m=1 is a "
                "later-slice extension"
            )
        n_shots = int(N)
        if n_shots < 1:
            raise ValueError(f"N must be >= 1, got {N!r}")

        import torch

        spt = self._shots_per_trajectory
        n_traj = (n_shots + spt - 1) // spt
        det_blocks: list[Any] = []
        obs_blocks: list[Any] = []
        truth_record: dict[str, Any] = {
            "seed": int(seed),
            "N": n_shots,
            "m": int(m),
            "shots_per_trajectory": spt,
            "n_trajectories": n_traj,
            "trajectory_seed_sample": [],
            "params_manifest_sample": [],
            "instrument_manifest_sample": None,
            "source_binding": None,
        }
        for j in range(n_traj):
            shots_j = min(spt, n_shots - j * spt)
            source_seed = _derived_seed(seed, j, "source")
            timeline = self._source.sample(seed=source_seed, n_cycles=self._rounds)
            params_cycles = self._fan_out(timeline, base_seed=seed, trajectory=j)
            self._assert_fan_out_alive(timeline, params_cycles)
            per_round = tuple(
                per_round_axis1_params(self._baseline_params, p) for p in params_cycles
            )
            instrument = trajectory_mean_instrument(params_cycles)
            det_table, obs_table, probabilities = self._tables_for(per_round, instrument)
            generator = torch.Generator(device=det_table.device).manual_seed(
                _derived_seed(seed, j, "sample")
            )
            sample_index = torch.multinomial(
                probabilities,
                num_samples=shots_j,
                replacement=True,
                generator=generator,
            )
            det_blocks.append(det_table.index_select(0, sample_index))
            obs_blocks.append(obs_table.index_select(0, sample_index))
            if j < _TRUTH_SEED_SAMPLE:
                truth_record["trajectory_seed_sample"].append(
                    {"trajectory": j, "source_seed": source_seed}
                )
            if j < _TRUTH_PARAMS_SAMPLE_TRAJECTORIES:
                truth_record["params_manifest_sample"].append(
                    {
                        "trajectory": j,
                        "per_cycle": [p.to_manifest() for p in params_cycles],
                    }
                )
            if j == 0:
                # the instrument / source-binding sample is a single representative (first trajectory).
                truth_record["instrument_manifest_sample"] = instrument.to_manifest()
                truth_record["source_binding"] = (
                    build_source_timeline_binding_manifest(
                        timeline,
                        binding=SourceTimelineBinding(cycle_binding="qec_round"),
                        compiled_metadata={"code_spec": self._spec.to_manifest()},
                        shots=shots_j,
                    )
                )
        det = torch.cat(det_blocks, dim=0).detach().to("cpu").numpy().astype(np.uint8)
        obs = (
            torch.cat(obs_blocks, dim=0)[:, 0]
            .detach()
            .to("cpu")
            .numpy()
            .astype(np.uint8)
        )
        # Evaluator-side bookkeeping only — never in the returned payload (C-7).
        self._last_emit = truth_record
        # C-3 (red-team R4): the emitted record payload is exactly {"det","obs"}.
        return {"det": det, "obs": obs}

    def channels(self) -> tuple[dict[str, Any], ...]:
        """Per-substep CPTP Kraus field at the mean-source Theta(0) point (S-2).

        Reuses the dense path's own selection plan + assembler so the reported
        field matches what the emitter applies, with per-round params replaced
        by the constant Theta(0) lowering (declared class-(c) mean-field
        simplification; per-shot fields are regenerable from truth seeds).
        """

        require_compiler_schedule_seal(self._sched)
        theta0 = per_round_axis1_params(
            self._baseline_params, source_to_params(0.0, self._config)
        )
        calibrations = _axis1_static_zz_calibrations_for_schedule(self._sched)
        selection_plan = build_axis1_schedule_selection_plan(self._sched)
        selection_partition = axis1_selection_layers_in_schedule_order(
            self._sched,
            selection_plan.selections,
            consumer_name="CoupledCycleNoiseProcess.channels",
        )
        rows: list[dict[str, Any]] = []
        for layer in selection_partition:
            for selection in layer.selections:
                dt = _nominal_positive_dt(selection)
                assembled = _assemble_selection_joint_channel(
                    selection,
                    dt_ns=dt,
                    params=theta0,
                    device=self._device,
                    static_zz_calibrations=calibrations,
                )
                round_index, is_terminal = self._round_map[selection.substep_id]
                rows.append(
                    {
                        "substep_id": selection.substep_id,
                        "selection_id": selection.selection_id,
                        "round_index": round_index,
                        "terminal": is_terminal,
                        "participant": tuple(int(q) for q in selection.participant),
                        "primitive_names": tuple(selection.primitive_names),
                        "dt_ns": float(dt),
                        "kraus": assembled.kraus,
                        "params_point": "theta_zero_mean_field",
                        "epistemic_class": "c",
                    }
                )
        return tuple(rows)

    def export_stim_circuit(self) -> tuple[Any, dict]:
        """P0 interop: the SAME compiled fixture as an ideal-geometry stim circuit.

        Recompiles ``self._spec`` through the same frontend compiler (a pure,
        deterministic function of the spec) and converts the ``CircuitIR`` via
        ``frontend.stim_io.circuit_to_stim``. The stim circuit is the ideal
        Clifford skeleton of the fixture — detectors and the logical observable
        in the record-layout declaration order, so its detector index ``k`` IS
        column ``k`` of the emitted ``det`` surface. DECLARED: the Axis-1
        analog (Lindblad) noise is NOT representable in this circuit; the
        decoder-facing noise summary is the separate
        ``frontend.interop.records_to_dem`` reduction of the emitted records.

        The export is a separate read-only surface — the ``emit`` payload
        stays exactly ``{"det","obs"}`` (C-3 untouched). Layout identity
        against the process's emitted surface is ASSERTED here (names, order,
        counts), never assumed.
        """

        from ..frontend.compiler import compile_code_spec
        from ..frontend.stim_io import circuit_to_stim, counts

        circuit_ir = compile_code_spec(self._spec)
        layout = circuit_ir.metadata["record_layout"]
        det_names = tuple(str(d["name"]) for d in layout["detectors"])
        obs_names = tuple(str(o["name"]) for o in layout["observables"])
        meas_keys = tuple(
            str(r["key"]) for r in layout["round_measurements"]
        ) + tuple(str(f["key"]) for f in layout["final_data"])
        if det_names != self._detector_names:
            raise RuntimeError(
                "export/emit detector layout mismatch: recompiled circuit "
                f"declares {det_names[:4]}... vs teacher {self._detector_names[:4]}..."
            )
        if obs_names != self._observable_names:
            raise RuntimeError(
                f"export/emit observable mismatch: {obs_names} vs "
                f"{self._observable_names}"
            )
        if meas_keys != self._measurement_keys:
            raise RuntimeError(
                "export/emit measurement-key mismatch between the recompiled "
                "circuit and the sealed schedule"
            )
        stim_circuit = circuit_to_stim(circuit_ir)
        stim_counts = counts(stim_circuit)
        if stim_counts.num_detectors != self._rounds * self._n_stab:
            raise RuntimeError(
                f"stim circuit has {stim_counts.num_detectors} detectors, "
                f"expected rounds*n_stab = {self._rounds * self._n_stab}"
            )
        if stim_counts.num_observables != 1:
            raise RuntimeError(
                f"stim circuit has {stim_counts.num_observables} observables, "
                "expected exactly 1"
            )
        if stim_counts.num_measurements != len(self._measurement_keys):
            raise RuntimeError(
                f"stim circuit has {stim_counts.num_measurements} measurements, "
                f"expected {len(self._measurement_keys)}"
            )
        manifest = {
            "schema": f"{COUPLED_TEACHER_SCHEMA}.stim_export.v1",
            "fixture": self._fixture,
            "code_spec_name": str(self._spec.name),
            "rounds": self._rounds,
            "n_stab": self._n_stab,
            "num_qubits": int(stim_counts.num_qubits),
            "num_detectors": int(stim_counts.num_detectors),
            "num_observables": int(stim_counts.num_observables),
            "num_measurements": int(stim_counts.num_measurements),
            "detector_names": list(det_names),
            "observable_names": list(obs_names),
            "measurement_keys": list(meas_keys),
            "det_column_semantics": (
                "stim detector index k == emitted det column k "
                "(record-layout declaration order)"
            ),
            "noise_representability": (
                "ideal Clifford geometry only; Axis-1 analog noise is not "
                "representable in the stim circuit (declared); decoder-facing "
                "noise summary = frontend.interop.records_to_dem"
            ),
        }
        return stim_circuit, manifest

    def emit_clifford_slice(
        self, regime: Any, *, p_x: float, m: int, N: int, seed: int
    ) -> dict:
        """Not implemented in slice 1 (declared).

        The stim-anchor wiring check needs a theta=0 / bit-flip ``X_ERROR(p_x)``
        Clifford slice of the SAME geometry; the dense Axis-1 path has no
        Pauli-noise injection seam (Stim noise is rejected by the schedule
        extractor by design), so wiring this slice is a later-slice cert
        anchor, not a slice-1 process capability.
        """

        raise NotImplementedError(
            "CoupledCycleNoiseProcess slice-1 has no Clifford/bit-flip emission seam; "
            "the stim wiring anchor is a later-slice extension"
        )

    # ------------------------------------------------------------------ #
    # ablation arms (C-9)                                                  #
    # ------------------------------------------------------------------ #
    def markovian_baseline(self) -> "CoupledCycleNoiseProcess":
        """The G6 negative control: matched marginals, broken coupling.

        Same source / config / schedule fixture; per-cycle params come from
        ``independent_baseline_trajectory_to_params`` (an independent
        permutation of the SAME trajectory per mechanism field — one-field
        marginals preserved exactly, same-cycle cross-mechanism and
        cross-cycle alignment destroyed).
        """

        return CoupledCycleNoiseProcess(
            self._rounds,
            source=self._source,
            config=self._config,
            shots_per_trajectory=self._shots_per_trajectory,
            device=self._device,
            code_spec_builder=self._code_spec_builder,
            fixture=self._fixture,
            coupling_arm="independent",
        )

    def off_source(self) -> "CoupledCycleNoiseProcess":
        """The collapse arm: amplitude-0 source => constant Theta(0) params."""

        if not hasattr(self._source, "amplitude_radns"):
            raise NotImplementedError(
                f"off_source requires an amplitude-bearing source; "
                f"{type(self._source).__name__} has no amplitude_radns field"
            )
        off = dataclasses.replace(
            self._source,
            amplitude_radns=0.0,
            name=f"{self._source.name}.off",
        )
        return CoupledCycleNoiseProcess(
            self._rounds,
            source=off,
            config=self._config,
            shots_per_trajectory=self._shots_per_trajectory,
            device=self._device,
            code_spec_builder=self._code_spec_builder,
            fixture=self._fixture,
            coupling_arm="off",
        )

    # ------------------------------------------------------------------ #
    # internals                                                            #
    # ------------------------------------------------------------------ #
    @property
    def coupling_arm(self) -> str:
        return self._arm

    @property
    def rounds(self) -> int:
        return self._rounds

    @property
    def n_stab(self) -> int:
        return self._n_stab

    def _validate_regime(self, regime: Any) -> None:
        """Regime consumption contract: R and n_stab are binding; the routing
        fields (register / n_active / arm / b) are not consumed by this
        process and are deliberately not validated."""

        regime_rounds = int(getattr(regime, "R"))
        if regime_rounds != self._rounds:
            raise ValueError(
                f"regime.R={regime_rounds} does not match the compiled schedule "
                f"rounds={self._rounds}; this teacher never re-compiles per emit"
            )
        regime_n_stab = getattr(regime, "n_stab", None)
        if regime_n_stab is not None and int(regime_n_stab) != self._n_stab:
            raise ValueError(
                f"regime.n_stab={regime_n_stab} does not match the fixture "
                f"n_stab={self._n_stab}"
            )

    def _fan_out(
        self, timeline: SourceTimeline, *, base_seed: int, trajectory: int
    ) -> tuple[CoupledMechanismParams, ...]:
        """Arm-dispatched Theta fan-out for one trajectory (C-2, C-9)."""

        z = timeline.payload_series("z_radns")
        if self._arm in {"shared", "off"}:
            if timeline.coupling_mode != "shared":
                raise ValueError(
                    "the shared/off arm requires a coupling_mode='shared' "
                    f"timeline, got {timeline.coupling_mode!r} (red-team R3)"
                )
            for marker in ("baseline", "baseline_of", "ablation", "ablation_of"):
                if marker in timeline.metadata:
                    raise ValueError(
                        f"timeline carries the {marker!r} marker; a permuted/"
                        "baseline timeline is not a valid shared arm (red-team R3)"
                    )
            return trajectory_to_params(z, self._config)
        # independent arm: per-field permutations of the SAME trajectory
        # (matched marginals) with a stable derived permutation seed.
        return independent_baseline_trajectory_to_params(
            z,
            self._config,
            seed=_derived_seed(base_seed, trajectory, "independent_permutation"),
        )

    def _assert_fan_out_alive(
        self,
        timeline: SourceTimeline,
        params_cycles: Sequence[CoupledMechanismParams],
    ) -> None:
        """Runtime R1 positive control: a non-constant trajectory with a live
        gamma_phi sensitivity MUST yield non-uniform per-cycle params."""

        if len(params_cycles) != self._rounds:
            raise ValueError(
                f"fan-out returned {len(params_cycles)} cycles for a "
                f"{self._rounds}-round schedule"
            )
        z = np.asarray(timeline.payload_series("z_radns"), dtype=np.float64)
        sens = abs(float(self._config.gamma_phi_sensitivity))
        sensitivity_live = sens > 0.0
        # "Non-constant" must mean z varies by MORE than the gamma_phi fan-out can resolve into distinct
        # float64 values: a z whose range is only ~ULP-scale legitimately fans out to a single gamma_phi
        # float (a DEGENERATE trajectory — arises once in ~1000s of realizations — not dead plumbing). The
        # bare np.unique(z).size >= 2 false-trips on such trajectories (red-team R1 false positive). Gate on
        # the map's own scale: two z values give distinct gamma_phi only when |dz| exceeds
        # ~(z_scale/sensitivity) * NUMERICAL_ZERO; below that the guard would demand a resolution the float
        # gamma_phi cannot carry. Genuine dead plumbing (z varies meaningfully, gamma_phi still uniform)
        # still raises.
        z_ptp = float(z.max() - z.min()) if z.size else 0.0
        z_scale = abs(float(self._config.z_scale_radns))
        z_resolution = (z_scale / sens) * NUMERICAL_ZERO if sens > 0.0 else float("inf")
        non_constant = z_ptp > z_resolution
        if non_constant and sensitivity_live:
            gammas = {float(p.gamma_phi_per_ns) for p in params_cycles}
            if len(gammas) < 2:
                raise RuntimeError(
                    "fan-out returned uniform gamma_phi for a non-constant "
                    "trajectory — dead per-round plumbing (red-team R1)"
                )

    def _tables_for(
        self,
        per_round: tuple[Axis1PrimitiveParams, ...],
        instrument: Axis1ReadoutResetInstrumentSpec,
    ) -> tuple[Any, Any, Any]:
        """ONE exact manifest call -> (det_table, obs_table, probabilities).

        Memoized on the exact (per-round params, instrument) key (S-6) —
        deterministic enumeration, so reuse is exact. The manifest's
        ``passed`` verdict gates sampling (C-6) and the record layout is
        asserted against the construction-derived layout every call.
        """

        import torch

        cache_key = (
            tuple(
                (
                    p.zeta_rad_per_ns,
                    p.gamma_phi_per_ns,
                    p.gamma_1_per_ns,
                    p.gamma_up_per_ns,
                    p.gamma_readout_phi_per_ns,
                    p.drive_area_rad,
                    p.drive_omega_rad_per_ns,
                    p.fsim_delta_theta_rad,
                    p.fsim_delta_phi_rad,
                )
                for p in per_round
            ),
            (
                instrument.readout_p0_to_1,
                instrument.readout_p1_to_0,
                instrument.readout_pair_flip_probability,
                instrument.reset_flip_probability,
            ),
        )
        cached = self._table_cache.get(cache_key)
        if cached is not None:
            return cached
        manifest = axis1_measurement_record_evidence_manifest(
            self._sched,
            device=self._device,
            instrument_spec=instrument,
            params_for_substep=params_for_substep_from_round_map(
                self._round_map, per_round
            ),
        )
        if manifest.get("passed") is not True:
            raise RuntimeError(
                "dense record manifest failed its own gate "
                f"(verdict={manifest.get('verdict')!r}); refusing to sample from "
                "a broken enumeration (C-6)"
            )
        record = manifest["record_evidence"]
        if tuple(str(k) for k in record["measurement_keys"]) != self._measurement_keys:
            raise RuntimeError(
                "measurement-key layout drifted between construction and emit"
            )
        if tuple(str(n) for n in record["detector_names"]) != self._detector_names:
            raise RuntimeError(
                "detector layout drifted between construction and emit"
            )
        if (
            tuple(str(n) for n in record["logical_observable_names"])
            != self._observable_names
        ):
            raise RuntimeError(
                "observable layout drifted between construction and emit"
            )
        det_table = torch.tensor(
            record["detector_records"], dtype=torch.uint8, device=self._device
        )
        obs_table = torch.tensor(
            record["logical_observable_records"], dtype=torch.uint8, device=self._device
        )
        if det_table.ndim != 2 or det_table.shape[1] != self._rounds * self._n_stab:
            raise RuntimeError(
                f"detector table width {tuple(det_table.shape)} != "
                f"(records, {self._rounds * self._n_stab})"
            )
        if obs_table.ndim != 2 or obs_table.shape[1] != 1:
            raise RuntimeError(
                f"observable table shape {tuple(obs_table.shape)} != (records, 1)"
            )
        probabilities = torch.tensor(
            record["record_probabilities"], dtype=torch.float64, device=self._device
        )
        if probabilities.ndim != 1 or probabilities.numel() != det_table.shape[0]:
            raise RuntimeError("record probability vector misaligned with tables")
        probabilities = probabilities / probabilities.sum()
        tables = (det_table, obs_table, probabilities)
        if len(self._table_cache) >= _TABLE_CACHE_MAX:
            self._table_cache.pop(next(iter(self._table_cache)))
        self._table_cache[cache_key] = tables
        return tables


__all__ = [
    "COUPLED_TEACHER_REPRESENTABILITY",
    "COUPLED_TEACHER_SCHEMA",
    "DEFAULT_STATIC_ZZ_EDGE",
    "MEMORYFUL_SHARED_SOURCES",
    "CoupledCycleNoiseProcess",
    "default_coupled_code_spec",
    "default_coupled_code_spec_4q",
    "default_coupled_code_spec_d3_repz",
    "derive_round_map_for_substep_schedule",
    "params_for_substep_from_round_map",
    "per_round_axis1_params",
    "trajectory_mean_instrument",
]

# Backward-compat alias — the ambiguous "Teacher" name is retired in error_coupling_simulator;
# qec_twin keeps it (its shim does globals().update(vars(this_module)), re-exporting both names).
CoupledCycleTeacher = CoupledCycleNoiseProcess
