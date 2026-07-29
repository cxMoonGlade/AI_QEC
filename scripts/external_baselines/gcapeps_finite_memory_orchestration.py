"""Pure outer orchestration for the frozen GCAPEPS finite-memory benchmark.

This module deliberately owns no systemd process lifecycle and imports no
candidate, reference, tensor-network, Clifford, or simulator implementation.
It supplies the deterministic calibration search, target-amendment, held-out
launch-plan, failure-propagation, and timing-aggregation logic that the root
runner can call after its system-manager preflight and per-node lifecycle have
passed.

It does not execute calibration or held-out science by itself.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import statistics
from typing import Any, Callable, Mapping, Sequence


SCHEMA_PREFIX = "error_coupling_simulator.external.gcapeps_finite_memory."
CALIBRATION_SCHEMA = SCHEMA_PREFIX + "calibration.v1"
CALIBRATION_PUBLICATION_RECEIPT_SCHEMA = (
    SCHEMA_PREFIX + "calibration_publication_receipt.v1"
)
TARGET_AMENDMENT_SCHEMA = SCHEMA_PREFIX + "calibration_amendment.v1"
HELDOUT_REPORT_SCHEMA = SCHEMA_PREFIX + "bond32_comparison.v1"
TIMING_SCHEMA = SCHEMA_PREFIX + "layered_timing.v1"
TRAILER_SCHEMA = SCHEMA_PREFIX + "late_telemetry_trailer.v1"
WALL_CLOCK = "time.perf_counter_ns"
CPU_CLOCK = "time.process_time_ns"
TERMINAL_CELL_ACCEPTANCE_SCHEMA = SCHEMA_PREFIX + "cell_acceptance.v1"


CALIBRATION = "CALIBRATION"
HELDOUT = "HELDOUT"

NEUTRAL_FIXTURE_EMITTER = "neutral_fixture_emitter"
DENSE_REFERENCE = "dense_reference"
PLAIN_CAP_PROBE = "plain_cap_probe"
GCAPEPS_CAP_PROBE = "gcapeps_cap_probe"
PLAIN_EVIDENCE = "plain_evidence"
GCAPEPS_EVIDENCE = "gcapeps_evidence"
PLAIN_PERFORMANCE = "plain_performance"
GCAPEPS_PERFORMANCE = "gcapeps_performance"
SDIM_COMPUTATION = "sdim_computation"
TERMINAL_COMPARATOR = "terminal_comparator"

TERMINAL_KINDS = frozenset(
    {
        "completed_result",
        "worker_censor",
        "supervisor_censor",
        "invalid_control",
    }
)
PERFORMANCE_ROLES = frozenset({PLAIN_PERFORMANCE, GCAPEPS_PERFORMANCE})

CALIBRATION_GAMMAS = (
    (0, "pi/11", "0x1.247426bd47de3p-2"),
    (1, "pi/9", "0x1.657184ae74487p-2"),
    (2, "pi/7", "0x1.cb91f3bbba140p-2"),
    (3, "pi/5", "0x1.41b2f769cf0e0p-1"),
)
CALIBRATION_ROUNDS = (4, 6, 8, 10, 12)
CALIBRATION_SEEDS = (0, 1, 2, 3)
CALIBRATION_WALL_NS = 12 * 60 * 60 * 1_000_000_000
MAX_PROBE_ATTEMPTS = 100
P_EVENT_NUMERATOR = 3
P_EVENT_DENOMINATOR = 4
HELDOUT_SEED = int.from_bytes(
    hashlib.sha256(b"gcapeps-finite-memory-heldout-v1").digest()[:8],
    "big",
)

CALIBRATION_PASS = "PASS"
CALIBRATION_INCOMPLETE = "CALIBRATION_INCOMPLETE_CENSORED"
CALIBRATION_INVALID = "CALIBRATION_INVALID_CONTROL_FAILURE"
CALIBRATION_NO_ELIGIBLE = "NO_ELIGIBLE_BOND32_NONMARKOVIAN_CELL"

HELDOUT_COMPLETE = "HELDOUT_COMPLETED"
HELDOUT_INCOMPLETE = "HELDOUT_INCOMPLETE_CENSORED"
HELDOUT_INVALID = "HELDOUT_INVALID_CONTROL_FAILURE"


def canonical_json_bytes(value: Any) -> bytes:
    """Encode one finite JSON value under the frozen canonical convention."""

    _validate_json_value(value, name="value")
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _validate_json_value(value: Any, *, name: str) -> None:
    if value is None or isinstance(value, (str, bool)):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{name} contains a nonfinite float")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_value(item, name=f"{name}[{index}]")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{name} has a non-string key")
            _validate_json_value(item, name=f"{name}.{key}")
        return
    raise ValueError(f"{name} contains a non-JSON value")


def _exact_keys(value: Mapping[str, Any], expected: set[str], *, name: str) -> None:
    actual = set(value)
    if actual != expected:
        raise ValueError(
            f"{name} keys differ: missing={sorted(expected - actual)!r}, "
            f"extra={sorted(actual - expected)!r}"
        )


def _plain_int(
    value: Any,
    *,
    name: str,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be a non-boolean integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} is below its minimum")
    if maximum is not None and value > maximum:
        raise ValueError(f"{name} is above its maximum")
    return value


def _finite_float(value: Any, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite JSON number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _sha256(value: Any, *, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or value.lower() != value
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{name} must be a lower-case SHA-256")
    return value


def _git_identity(value: Mapping[str, Any], *, name: str) -> None:
    _exact_keys(value, {"commit", "tree"}, name=name)
    for key in ("commit", "tree"):
        digest = value[key]
        if (
            not isinstance(digest, str)
            or len(digest) not in {40, 64}
            or digest.lower() != digest
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise ValueError(f"{name}.{key} is not a full Git identity")


def _projection_sha256(value: Mapping[str, Any]) -> str:
    projected = dict(value)
    projected.pop("result_projection_sha256", None)
    return canonical_sha256(projected)


def _with_projection(value: Mapping[str, Any]) -> dict[str, Any]:
    if "result_projection_sha256" in value:
        raise ValueError("projection hash may be added only once")
    result = dict(value)
    result["result_projection_sha256"] = _projection_sha256(result)
    return result


def _validate_projection(
    value: Mapping[str, Any],
    *,
    forbidden_self_keys: Sequence[str] = (),
) -> None:
    for key in forbidden_self_keys:
        if key in value:
            raise ValueError(f"forbidden self-identity key: {key}")
    _sha256(
        value.get("result_projection_sha256"),
        name="result_projection_sha256",
    )
    if value["result_projection_sha256"] != _projection_sha256(value):
        raise ValueError("result projection SHA-256 mismatch")


def _freeze_parameters(value: Mapping[str, Any]) -> tuple[tuple[str, Any], ...]:
    _validate_json_value(value, name="role_parameters")
    return tuple(sorted(value.items()))


@dataclass(frozen=True)
class CalibrationPair:
    gamma_index: int
    gamma_label: str
    gamma_float64_hex: str
    rounds_index: int
    rounds: int

    @property
    def pair_id(self) -> str:
        return f"g{self.gamma_index:02d}-r{self.rounds_index:02d}"


@dataclass(frozen=True)
class LaunchSpec:
    ordinal: int
    run_partition: str
    phase: str
    case_id: str
    launch_id: str
    role: str
    role_parameters: tuple[tuple[str, Any], ...]
    dependency_launch_ids: tuple[str, ...] = ()
    consumes_probe_attempt: bool = False
    workflow_ordinal: int | None = None

    def parameter_map(self) -> dict[str, Any]:
        return dict(self.role_parameters)


@dataclass(frozen=True)
class NodeObservation:
    """Normalized final node identity returned by a fake or real launcher.

    ``qualifier`` is role-scoped: dense uses the registered fixed-mask
    max-increment gate; cap probes and full evidence use the registered
    positive-tail gate; the comparator uses complete calibration terminal-gate PASS.
    No fidelity value is accepted here, so it cannot influence calibration.
    """

    terminal_kind: str
    qualifier: bool | None
    envelope_complete_file_sha256: str
    launch_receipt_complete_file_sha256: str

    def validate_for(self, spec: LaunchSpec) -> None:
        if self.terminal_kind not in TERMINAL_KINDS:
            raise ValueError("node observation has an invalid terminal kind")
        _sha256(
            self.envelope_complete_file_sha256,
            name="envelope_complete_file_sha256",
        )
        _sha256(
            self.launch_receipt_complete_file_sha256,
            name="launch_receipt_complete_file_sha256",
        )
        qualifier_roles = {
            DENSE_REFERENCE,
            PLAIN_CAP_PROBE,
            GCAPEPS_CAP_PROBE,
            PLAIN_EVIDENCE,
            GCAPEPS_EVIDENCE,
            TERMINAL_COMPARATOR,
        }
        if self.terminal_kind == "completed_result":
            if spec.role in qualifier_roles:
                if not isinstance(self.qualifier, bool):
                    raise ValueError(
                        "completed qualifying role must report a boolean qualifier"
                    )
            elif self.qualifier is not None:
                raise ValueError(
                    "completed non-qualifying role must not report a qualifier"
                )
        elif self.qualifier is not None:
            raise ValueError("non-completed node cannot report a qualifier")


@dataclass(frozen=True)
class LaunchAudit:
    spec: LaunchSpec
    executed: bool
    disposition: str
    terminal_kind: str | None
    qualifier: bool | None
    envelope_complete_file_sha256: str | None
    launch_receipt_complete_file_sha256: str | None
    prelaunch_wall_offset_ns: int | None = None
    terminal_wall_offset_ns: int | None = None
    probe_attempt_before: int | None = None
    probe_attempt_after: int | None = None


@dataclass(frozen=True)
class StageSeedAudit:
    pair_id: str
    stage: str
    seed: int
    disposition: str
    launch_ids: tuple[str, ...]


@dataclass(frozen=True)
class CalibrationSelection:
    pair: CalibrationPair
    qualifying_seeds: tuple[int, int]


@dataclass(frozen=True)
class CalibrationSearchResult:
    wall_root_ns: int
    wall_deadline_ns: int
    probe_attempt_count: int
    prepublication_disposition: str
    selection: CalibrationSelection | None
    launch_audit: tuple[LaunchAudit, ...]
    stage_seed_audit: tuple[StageSeedAudit, ...]


def build_calibration_pairs() -> tuple[CalibrationPair, ...]:
    """Return the exact 20-pair displayed-ordinal calibration search."""

    return tuple(
        CalibrationPair(
            gamma_index=gamma_index,
            gamma_label=gamma_label,
            gamma_float64_hex=gamma_hex,
            rounds_index=rounds_index,
            rounds=rounds,
        )
        for gamma_index, gamma_label, gamma_hex in CALIBRATION_GAMMAS
        for rounds_index, rounds in enumerate(CALIBRATION_ROUNDS)
    )


def next_probe_attempt(current_count: int) -> int:
    """Increment immediately before a B/C launch; attempt 100 is legal."""

    current_count = _plain_int(
        current_count,
        name="current_count",
        minimum=0,
        maximum=MAX_PROBE_ATTEMPTS,
    )
    if current_count == MAX_PROBE_ATTEMPTS:
        raise RuntimeError("calibration probe attempt 101 is forbidden")
    return current_count + 1


def _calibration_case_id(pair: CalibrationPair, seed: int) -> str:
    return (
        f"calibration-g{pair.gamma_index}-s{seed}-"
        f"w7-r{pair.rounds}-a3-p3of4"
    )


def _launch_spec(
    *,
    ordinal: int,
    run_partition: str,
    phase: str,
    case_id: str,
    launch_id: str,
    role: str,
    role_parameters: Mapping[str, Any],
    dependencies: Sequence[str] = (),
    consumes_probe_attempt: bool = False,
    workflow_ordinal: int | None = None,
) -> LaunchSpec:
    if run_partition not in {CALIBRATION, HELDOUT}:
        raise ValueError("unsupported launch partition")
    if not launch_id or any(
        character not in "abcdefghijklmnopqrstuvwxyz0123456789-"
        for character in launch_id
    ):
        raise ValueError("launch_id is outside the lowercase service namespace")
    return LaunchSpec(
        ordinal=_plain_int(ordinal, name="ordinal", minimum=0),
        run_partition=run_partition,
        phase=phase,
        case_id=case_id,
        launch_id=launch_id,
        role=role,
        role_parameters=_freeze_parameters(role_parameters),
        dependency_launch_ids=tuple(dependencies),
        consumes_probe_attempt=consumes_probe_attempt,
        workflow_ordinal=workflow_ordinal,
    )


class _CalibrationHalt(RuntimeError):
    def __init__(self, disposition: str) -> None:
        super().__init__(disposition)
        self.disposition = disposition


def run_calibration_search(
    launch_one: Callable[[LaunchSpec], NodeObservation],
    *,
    clock_ns: Callable[[], int],
) -> CalibrationSearchResult:
    """Execute the frozen adaptive search against an injected serial launcher.

    The callback must return an already-finalized node observation, meaning the
    envelope and launch receipt were published only after cleanup, unload, and
    quarantine.  This function never launches a claim-bearing run in tests; the
    callback seam exists so the exact graph can be exercised with fakes.
    """

    root = _plain_int(clock_ns(), name="wall_root_ns", minimum=0)
    deadline = root + CALIBRATION_WALL_NS
    launches: list[LaunchAudit] = []
    stages: list[StageSeedAudit] = []
    ordinal = 0
    attempts = 0
    selection: CalibrationSelection | None = None
    final = CALIBRATION_NO_ELIGIBLE

    def execute(spec: LaunchSpec) -> NodeObservation:
        nonlocal ordinal, attempts
        if spec.ordinal != ordinal:
            raise AssertionError("internal launch ordinal drift")
        now = _plain_int(clock_ns(), name="prelaunch_clock_ns", minimum=0)
        prelaunch_offset = now - root
        attempt_before = attempts
        if now >= deadline:
            launches.append(
                LaunchAudit(
                    spec=spec,
                    executed=False,
                    disposition="SKIPPED_DEADLINE_CENSOR",
                    terminal_kind=None,
                    qualifier=None,
                    envelope_complete_file_sha256=None,
                    launch_receipt_complete_file_sha256=None,
                    prelaunch_wall_offset_ns=prelaunch_offset,
                    terminal_wall_offset_ns=prelaunch_offset,
                    probe_attempt_before=attempt_before,
                    probe_attempt_after=attempts,
                )
            )
            raise _CalibrationHalt(CALIBRATION_INCOMPLETE)
        if spec.consumes_probe_attempt:
            try:
                attempts = next_probe_attempt(attempts)
            except RuntimeError:
                launches.append(
                    LaunchAudit(
                        spec=spec,
                        executed=False,
                        disposition="SKIPPED_ATTEMPT_101_CENSOR",
                        terminal_kind=None,
                        qualifier=None,
                        envelope_complete_file_sha256=None,
                        launch_receipt_complete_file_sha256=None,
                        prelaunch_wall_offset_ns=prelaunch_offset,
                        terminal_wall_offset_ns=prelaunch_offset,
                        probe_attempt_before=attempt_before,
                        probe_attempt_after=attempts,
                    )
                )
                raise _CalibrationHalt(CALIBRATION_INCOMPLETE)
            if spec.parameter_map()["attempt_ordinal"] != attempts:
                raise AssertionError("attempt ordinal was not bound pre-launch")
        observation = launch_one(spec)
        if not isinstance(observation, NodeObservation):
            raise TypeError("launch callback returned the wrong observation type")
        observation.validate_for(spec)
        terminal_now = _plain_int(
            clock_ns(), name="terminal_clock_ns", minimum=now
        )
        terminal_offset = terminal_now - root
        launches.append(
            LaunchAudit(
                spec=spec,
                executed=True,
                disposition=observation.terminal_kind,
                terminal_kind=observation.terminal_kind,
                qualifier=observation.qualifier,
                envelope_complete_file_sha256=(
                    observation.envelope_complete_file_sha256
                ),
                launch_receipt_complete_file_sha256=(
                    observation.launch_receipt_complete_file_sha256
                ),
                prelaunch_wall_offset_ns=prelaunch_offset,
                terminal_wall_offset_ns=terminal_offset,
                probe_attempt_before=attempt_before,
                probe_attempt_after=attempts,
            )
        )
        ordinal += 1
        if (
            terminal_now > deadline
            and observation.terminal_kind == "completed_result"
        ):
            raise _CalibrationHalt(CALIBRATION_INVALID)
        if observation.terminal_kind == "invalid_control":
            raise _CalibrationHalt(CALIBRATION_INVALID)
        if observation.terminal_kind in {
            "worker_censor",
            "supervisor_censor",
        }:
            raise _CalibrationHalt(CALIBRATION_INCOMPLETE)
        return observation

    try:
        for pair in build_calibration_pairs():
            fixtures: dict[int, str] = {}
            a_positive: dict[int, bool] = {}
            for seed in CALIBRATION_SEEDS:
                case_id = _calibration_case_id(pair, seed)
                fixture_id = f"cal-{pair.pair_id}-s{seed}-fixture"
                fixture = _launch_spec(
                    ordinal=ordinal,
                    run_partition=CALIBRATION,
                    phase="A_FIXTURE",
                    case_id=case_id,
                    launch_id=fixture_id,
                    role=NEUTRAL_FIXTURE_EMITTER,
                    role_parameters={
                        "width": 7,
                        "rounds": pair.rounds,
                        "axis_family": 3,
                        "p_event_numerator": 3,
                        "p_event_denominator": 4,
                        "seed": seed,
                        "gamma_index": pair.gamma_index,
                        "run_blpensemble": False,
                        "rounds_index": pair.rounds_index,
                    },
                )
                execute(fixture)
                fixtures[seed] = fixture_id
                dense_id = f"cal-{pair.pair_id}-s{seed}-dense"
                dense = _launch_spec(
                    ordinal=ordinal,
                    run_partition=CALIBRATION,
                    phase="A",
                    case_id=case_id,
                    launch_id=dense_id,
                    role=DENSE_REFERENCE,
                    role_parameters={
                        "gamma_index": pair.gamma_index,
                        "rounds_index": pair.rounds_index,
                        "seed": seed,
                        "calibration_stage": "A",
                    },
                    dependencies=(fixture_id,),
                )
                outcome = execute(dense)
                a_positive[seed] = bool(outcome.qualifier)
                stages.append(
                    StageSeedAudit(
                        pair_id=pair.pair_id,
                        stage="A",
                        seed=seed,
                        disposition=(
                            "COMPLETED_POSITIVE"
                            if outcome.qualifier
                            else "COMPLETED_SCIENTIFIC_NEGATIVE"
                        ),
                        launch_ids=(fixture_id, dense_id),
                    )
                )

            b_positive: dict[int, bool] = {}
            for seed in CALIBRATION_SEEDS:
                if not a_positive[seed]:
                    stages.append(
                        StageSeedAudit(
                            pair_id=pair.pair_id,
                            stage="B",
                            seed=seed,
                            disposition="SKIPPED_NOT_A_POSITIVE",
                            launch_ids=(),
                        )
                    )
                    b_positive[seed] = False
                    continue
                results: list[bool] = []
                ids: list[str] = []
                for input_id in (1, 2):
                    attempt = attempts + 1
                    launch_id = (
                        f"cal-{pair.pair_id}-s{seed}-plain-probe-i{input_id}"
                    )
                    spec = _launch_spec(
                        ordinal=ordinal,
                        run_partition=CALIBRATION,
                        phase="B",
                        case_id=_calibration_case_id(pair, seed),
                        launch_id=launch_id,
                        role=PLAIN_CAP_PROBE,
                        role_parameters={
                            "gamma_index": pair.gamma_index,
                            "rounds_index": pair.rounds_index,
                            "seed": seed,
                            "calibration_stage": "B",
                            "input_id": input_id,
                            "attempt_ordinal": attempt,
                        },
                        dependencies=(fixtures[seed],),
                        consumes_probe_attempt=True,
                    )
                    results.append(bool(execute(spec).qualifier))
                    ids.append(launch_id)
                b_positive[seed] = all(results)
                stages.append(
                    StageSeedAudit(
                        pair_id=pair.pair_id,
                        stage="B",
                        seed=seed,
                        disposition=(
                            "COMPLETED_POSITIVE"
                            if b_positive[seed]
                            else "COMPLETED_SCIENTIFIC_NEGATIVE"
                        ),
                        launch_ids=tuple(ids),
                    )
                )

            c_positive: dict[int, bool] = {}
            for seed in CALIBRATION_SEEDS:
                if not b_positive[seed]:
                    stages.append(
                        StageSeedAudit(
                            pair_id=pair.pair_id,
                            stage="C",
                            seed=seed,
                            disposition="SKIPPED_NOT_B_POSITIVE",
                            launch_ids=(),
                        )
                    )
                    c_positive[seed] = False
                    continue
                results = []
                ids = []
                for input_id in (1, 2):
                    attempt = attempts + 1
                    launch_id = (
                        f"cal-{pair.pair_id}-s{seed}-gc-probe-i{input_id}"
                    )
                    spec = _launch_spec(
                        ordinal=ordinal,
                        run_partition=CALIBRATION,
                        phase="C",
                        case_id=_calibration_case_id(pair, seed),
                        launch_id=launch_id,
                        role=GCAPEPS_CAP_PROBE,
                        role_parameters={
                            "gamma_index": pair.gamma_index,
                            "rounds_index": pair.rounds_index,
                            "seed": seed,
                            "calibration_stage": "C",
                            "input_id": input_id,
                            "attempt_ordinal": attempt,
                        },
                        dependencies=(fixtures[seed],),
                        consumes_probe_attempt=True,
                    )
                    results.append(bool(execute(spec).qualifier))
                    ids.append(launch_id)
                c_positive[seed] = all(results)
                stages.append(
                    StageSeedAudit(
                        pair_id=pair.pair_id,
                        stage="C",
                        seed=seed,
                        disposition=(
                            "COMPLETED_POSITIVE"
                            if c_positive[seed]
                            else "COMPLETED_SCIENTIFIC_NEGATIVE"
                        ),
                        launch_ids=tuple(ids),
                    )
                )

            qualifying_seeds: list[int] = []
            for seed in CALIBRATION_SEEDS:
                if not c_positive[seed]:
                    stages.append(
                        StageSeedAudit(
                            pair_id=pair.pair_id,
                            stage="D",
                            seed=seed,
                            disposition="SKIPPED_NOT_AC_PREQUALIFIED",
                            launch_ids=(),
                        )
                    )
                    continue
                ids = []
                evidence_ids: list[str] = []
                for lane, role in (
                    ("plain", PLAIN_EVIDENCE),
                    ("gc", GCAPEPS_EVIDENCE),
                ):
                    for input_id in (1, 2):
                        launch_id = (
                            f"cal-{pair.pair_id}-s{seed}-{lane}-evidence-"
                            f"i{input_id}"
                        )
                        spec = _launch_spec(
                            ordinal=ordinal,
                            run_partition=CALIBRATION,
                            phase="D",
                            case_id=_calibration_case_id(pair, seed),
                            launch_id=launch_id,
                            role=role,
                            role_parameters={
                                "gamma_index": pair.gamma_index,
                                "rounds_index": pair.rounds_index,
                                "seed": seed,
                                "calibration_stage": "D",
                                "input_id": input_id,
                            },
                            dependencies=(fixtures[seed],),
                        )
                        result = execute(spec)
                        if result.qualifier is not True:
                            raise _CalibrationHalt(CALIBRATION_INVALID)
                        ids.append(launch_id)
                        evidence_ids.append(launch_id)
                sdim_id = f"cal-{pair.pair_id}-s{seed}-sdim"
                execute(
                    _launch_spec(
                        ordinal=ordinal,
                        run_partition=CALIBRATION,
                        phase="D",
                        case_id=_calibration_case_id(pair, seed),
                        launch_id=sdim_id,
                        role=SDIM_COMPUTATION,
                        role_parameters={
                            "gamma_index": pair.gamma_index,
                            "rounds_index": pair.rounds_index,
                            "seed": seed,
                            "calibration_stage": "D",
                        },
                        dependencies=(fixtures[seed],),
                    )
                )
                ids.append(sdim_id)
                comparator_id = f"cal-{pair.pair_id}-s{seed}-comparator"
                comparator = execute(
                    _launch_spec(
                        ordinal=ordinal,
                        run_partition=CALIBRATION,
                        phase="D",
                        case_id=_calibration_case_id(pair, seed),
                        launch_id=comparator_id,
                        role=TERMINAL_COMPARATOR,
                        role_parameters={
                            "gamma_index": pair.gamma_index,
                            "rounds_index": pair.rounds_index,
                            "seed": seed,
                            "calibration_stage": "D",
                        },
                        dependencies=(
                            fixtures[seed],
                            f"cal-{pair.pair_id}-s{seed}-dense",
                            *evidence_ids,
                            sdim_id,
                        ),
                    )
                )
                ids.append(comparator_id)
                if comparator.qualifier is not True:
                    raise _CalibrationHalt(CALIBRATION_INVALID)
                qualifying_seeds.append(seed)
                stages.append(
                    StageSeedAudit(
                        pair_id=pair.pair_id,
                        stage="D",
                        seed=seed,
                        disposition="PASS",
                        launch_ids=tuple(ids),
                    )
                )
                if len(qualifying_seeds) == 2:
                    selection = CalibrationSelection(
                        pair=pair,
                        qualifying_seeds=(
                            qualifying_seeds[0],
                            qualifying_seeds[1],
                        ),
                    )
                    final = CALIBRATION_PASS
                    break
            if selection is not None:
                break
    except _CalibrationHalt as halt:
        final = halt.disposition

    stage_rows = {
        (row.pair_id, row.stage, row.seed): row
        for row in stages
    }
    if len(stage_rows) != len(stages):
        raise AssertionError("duplicate calibration stage/seed audit row")
    complete_stage_rows: list[StageSeedAudit] = []
    selected_pair_id = (
        selection.pair.pair_id if selection is not None else None
    )
    selected_pair_seen = False
    for pair in build_calibration_pairs():
        if pair.pair_id == selected_pair_id:
            selected_pair_seen = True
        for stage in ("A", "B", "C", "D"):
            for seed in CALIBRATION_SEEDS:
                key = (pair.pair_id, stage, seed)
                existing = stage_rows.get(key)
                if existing is not None:
                    complete_stage_rows.append(existing)
                    continue
                if final == CALIBRATION_PASS:
                    if pair.pair_id == selected_pair_id:
                        disposition = "FORBIDDEN_AFTER_SECOND_STAGE_D_PASS"
                    elif selected_pair_seen:
                        disposition = "FORBIDDEN_AFTER_SELECTION"
                    else:
                        raise AssertionError(
                            "pre-selection stage audit row is missing"
                        )
                elif final in {CALIBRATION_INCOMPLETE, CALIBRATION_INVALID}:
                    disposition = "SKIPPED_AFTER_CALIBRATION_TERMINAL"
                else:
                    raise AssertionError(
                        "complete-grid calibration audit row is missing"
                    )
                complete_stage_rows.append(
                    StageSeedAudit(
                        pair_id=pair.pair_id,
                        stage=stage,
                        seed=seed,
                        disposition=disposition,
                        launch_ids=(),
                    )
                )

    return CalibrationSearchResult(
        wall_root_ns=root,
        wall_deadline_ns=deadline,
        probe_attempt_count=attempts,
        prepublication_disposition=final,
        selection=selection,
        launch_audit=tuple(launches),
        stage_seed_audit=tuple(complete_stage_rows),
    )


def _launch_audit_json(row: LaunchAudit) -> dict[str, Any]:
    return {
        "ordinal": row.spec.ordinal,
        "run_partition": row.spec.run_partition,
        "phase": row.spec.phase,
        "case_id": row.spec.case_id,
        "launch_id": row.spec.launch_id,
        "role": row.spec.role,
        "role_parameters": row.spec.parameter_map(),
        "dependency_launch_ids": list(row.spec.dependency_launch_ids),
        "consumes_probe_attempt": row.spec.consumes_probe_attempt,
        "executed": row.executed,
        "disposition": row.disposition,
        "terminal_kind": row.terminal_kind,
        "qualifier": row.qualifier,
        "envelope_complete_file_sha256": row.envelope_complete_file_sha256,
        "launch_receipt_complete_file_sha256": (
            row.launch_receipt_complete_file_sha256
        ),
        "prelaunch_wall_offset_ns": row.prelaunch_wall_offset_ns,
        "terminal_wall_offset_ns": row.terminal_wall_offset_ns,
        "probe_attempt_before": row.probe_attempt_before,
        "probe_attempt_after": row.probe_attempt_after,
    }


def build_calibration_report(
    result: CalibrationSearchResult,
    *,
    identity_bindings: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the pre-publication report; it never self-claims publication."""

    validate_supporting_identities(identity_bindings)
    selection: dict[str, Any] | None
    if result.selection is None:
        selection = None
    else:
        pair = result.selection.pair
        selection = {
            "gamma_index": pair.gamma_index,
            "gamma_label": pair.gamma_label,
            "gamma_float64_hex": pair.gamma_float64_hex,
            "rounds_index": pair.rounds_index,
            "rounds_star": pair.rounds,
            "p_event_numerator": P_EVENT_NUMERATOR,
            "p_event_denominator": P_EVENT_DENOMINATOR,
            "qualifying_seeds": list(result.selection.qualifying_seeds),
        }
    payload = {
        "schema": CALIBRATION_SCHEMA,
        "run_partition": CALIBRATION,
        "prepublication_disposition": result.prepublication_disposition,
        "wall_root_ns": result.wall_root_ns,
        "wall_deadline_ns": result.wall_deadline_ns,
        "wall_budget_ns": CALIBRATION_WALL_NS,
        "probe_attempt_count": result.probe_attempt_count,
        "probe_attempt_ceiling": MAX_PROBE_ATTEMPTS,
        "selection": selection,
        "launch_audit": [_launch_audit_json(row) for row in result.launch_audit],
        "stage_seed_audit": [
            {
                "pair_id": row.pair_id,
                "stage": row.stage,
                "seed": row.seed,
                "disposition": row.disposition,
                "launch_ids": list(row.launch_ids),
            }
            for row in result.stage_seed_audit
        ],
        "identity_bindings": dict(identity_bindings),
        "claims_publication_completed": False,
    }
    return _with_projection(payload)


def validate_calibration_report(value: Mapping[str, Any]) -> None:
    _exact_keys(
        value,
        {
            "schema",
            "run_partition",
            "prepublication_disposition",
            "wall_root_ns",
            "wall_deadline_ns",
            "wall_budget_ns",
            "probe_attempt_count",
            "probe_attempt_ceiling",
            "selection",
            "launch_audit",
            "stage_seed_audit",
            "identity_bindings",
            "claims_publication_completed",
            "result_projection_sha256",
        },
        name="calibration report",
    )
    if value["schema"] != CALIBRATION_SCHEMA or value["run_partition"] != CALIBRATION:
        raise ValueError("calibration report identity drifted")
    if value["prepublication_disposition"] not in {
        CALIBRATION_PASS,
        CALIBRATION_INCOMPLETE,
        CALIBRATION_INVALID,
        CALIBRATION_NO_ELIGIBLE,
    }:
        raise ValueError("calibration disposition is invalid")
    root = _plain_int(value["wall_root_ns"], name="wall_root_ns", minimum=0)
    if value["wall_deadline_ns"] != root + CALIBRATION_WALL_NS:
        raise ValueError("calibration deadline drifted")
    if (
        value["wall_budget_ns"] != CALIBRATION_WALL_NS
        or value["probe_attempt_ceiling"] != MAX_PROBE_ATTEMPTS
    ):
        raise ValueError("calibration ceiling drifted")
    _plain_int(
        value["probe_attempt_count"],
        name="probe_attempt_count",
        minimum=0,
        maximum=MAX_PROBE_ATTEMPTS,
    )
    if value["claims_publication_completed"] is not False:
        raise ValueError("calibration report cannot self-claim publication")
    validate_supporting_identities(value["identity_bindings"])
    if value["prepublication_disposition"] == CALIBRATION_PASS:
        _validate_selection(value["selection"])
    elif value["selection"] is not None:
        raise ValueError("non-PASS calibration cannot carry a selection")
    if not isinstance(value["launch_audit"], list) or not isinstance(
        value["stage_seed_audit"], list
    ):
        raise ValueError("calibration audit rows must be lists")
    _validate_projection(
        value,
        forbidden_self_keys=("complete_file_sha256",),
    )


def _validate_selection(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("calibration PASS requires a selection object")
    _exact_keys(
        value,
        {
            "gamma_index",
            "gamma_label",
            "gamma_float64_hex",
            "rounds_index",
            "rounds_star",
            "p_event_numerator",
            "p_event_denominator",
            "qualifying_seeds",
        },
        name="calibration selection",
    )
    gamma_index = _plain_int(
        value["gamma_index"], name="gamma_index", minimum=0, maximum=3
    )
    rounds_index = _plain_int(
        value["rounds_index"], name="rounds_index", minimum=0, maximum=4
    )
    gamma = CALIBRATION_GAMMAS[gamma_index]
    if (
        value["gamma_label"] != gamma[1]
        or value["gamma_float64_hex"] != gamma[2]
        or value["rounds_star"] != CALIBRATION_ROUNDS[rounds_index]
        or value["p_event_numerator"] != 3
        or value["p_event_denominator"] != 4
    ):
        raise ValueError("calibration selection drifted from the displayed grid")
    seeds = value["qualifying_seeds"]
    if (
        not isinstance(seeds, list)
        or len(seeds) != 2
        or seeds != sorted(seeds)
        or len(set(seeds)) != 2
        or any(seed not in CALIBRATION_SEEDS for seed in seeds)
    ):
        raise ValueError("qualifying seeds must be two distinct ascending seeds")


def build_calibration_publication_receipt(
    *,
    report_path: str,
    report: Mapping[str, Any],
    report_byte_length: int,
    report_complete_file_sha256: str,
    publication_start_offset_ns: int,
    publication_committed_offset_ns: int,
    publication_gates: Mapping[str, bool],
) -> dict[str, Any]:
    """Bind report publication and assign the unique post-publication class."""

    validate_calibration_report(report)
    report_raw = canonical_json_bytes(report)
    if report_byte_length != len(report_raw):
        raise ValueError("calibration report byte length mismatch")
    if report_complete_file_sha256 != hashlib.sha256(report_raw).hexdigest():
        raise ValueError("calibration report complete-file SHA-256 mismatch")
    expected_gates = {
        "temporary_file_fsync",
        "rename_noreplace",
        "parent_directory_fsync",
        "destination_reopen_nofollow",
        "destination_identity_match",
        "exact_byte_reread",
    }
    _exact_keys(publication_gates, expected_gates, name="publication_gates")
    if any(value is not True for value in publication_gates.values()):
        raise ValueError("every calibration publication gate must pass")
    start = _plain_int(
        publication_start_offset_ns,
        name="publication_start_offset_ns",
        minimum=0,
    )
    committed = _plain_int(
        publication_committed_offset_ns,
        name="publication_committed_offset_ns",
        minimum=start,
    )
    committed_by_deadline = committed <= CALIBRATION_WALL_NS
    pre = report["prepublication_disposition"]
    if pre in {CALIBRATION_PASS, CALIBRATION_NO_ELIGIBLE}:
        final = pre if committed_by_deadline else CALIBRATION_INVALID
    else:
        final = pre
    payload = {
        "schema": CALIBRATION_PUBLICATION_RECEIPT_SCHEMA,
        "report_path": report_path,
        "report_schema": CALIBRATION_SCHEMA,
        "report_result_projection_sha256": report["result_projection_sha256"],
        "report_byte_length": report_byte_length,
        "report_complete_file_sha256": report_complete_file_sha256,
        "prepublication_disposition": pre,
        "wall_root_ns": report["wall_root_ns"],
        "wall_deadline_ns": report["wall_deadline_ns"],
        "publication_start_offset_ns": start,
        "publication_committed_offset_ns": committed,
        "publication_gates": dict(publication_gates),
        "committed_by_deadline": committed_by_deadline,
        "final_calibration_class": final,
    }
    return _with_projection(payload)


def validate_calibration_publication_receipt(
    value: Mapping[str, Any],
    *,
    report: Mapping[str, Any],
) -> None:
    validate_calibration_report(report)
    _exact_keys(
        value,
        {
            "schema",
            "report_path",
            "report_schema",
            "report_result_projection_sha256",
            "report_byte_length",
            "report_complete_file_sha256",
            "prepublication_disposition",
            "wall_root_ns",
            "wall_deadline_ns",
            "publication_start_offset_ns",
            "publication_committed_offset_ns",
            "publication_gates",
            "committed_by_deadline",
            "final_calibration_class",
            "result_projection_sha256",
        },
        name="calibration publication receipt",
    )
    if (
        value["schema"] != CALIBRATION_PUBLICATION_RECEIPT_SCHEMA
        or value["report_schema"] != CALIBRATION_SCHEMA
        or value["report_result_projection_sha256"]
        != report["result_projection_sha256"]
        or value["prepublication_disposition"]
        != report["prepublication_disposition"]
        or value["wall_root_ns"] != report["wall_root_ns"]
        or value["wall_deadline_ns"] != report["wall_deadline_ns"]
    ):
        raise ValueError("calibration publication receipt binding drifted")
    raw = canonical_json_bytes(report)
    if (
        value["report_byte_length"] != len(raw)
        or value["report_complete_file_sha256"]
        != hashlib.sha256(raw).hexdigest()
    ):
        raise ValueError("receipt does not bind exact calibration report bytes")
    committed = _plain_int(
        value["publication_committed_offset_ns"],
        name="publication_committed_offset_ns",
        minimum=0,
    )
    expected_timely = committed <= CALIBRATION_WALL_NS
    if value["committed_by_deadline"] is not expected_timely:
        raise ValueError("receipt committed_by_deadline drifted")
    pre = value["prepublication_disposition"]
    expected_final = (
        pre
        if pre not in {CALIBRATION_PASS, CALIBRATION_NO_ELIGIBLE}
        or expected_timely
        else CALIBRATION_INVALID
    )
    if value["final_calibration_class"] != expected_final:
        raise ValueError("receipt final calibration class drifted")
    _validate_projection(
        value,
        forbidden_self_keys=("complete_file_sha256",),
    )


_SUPPORTING_IDENTITY_KEYS = {
    "source_documents",
    "theory_checkpoint",
    "theory_erratum_checkpoint",
    "implementations",
    "environment",
    "sdim",
    "manager_preflight",
    "result_schemas",
    "mask_contract",
}
_SOURCE_DOCUMENT_KEYS = {
    "literature_closure",
    "preregistration",
    "metrics",
    "numerical_provenance",
    "partial_swap_sign_audit",
    "partial_swap_sign_independent_review",
    "independent_preregistration_rereview",
    "theory_erratum_rereview",
}


def validate_supporting_identities(value: Mapping[str, Any]) -> None:
    """Validate the amendment/report identity packet without attesting it."""

    if not isinstance(value, Mapping):
        raise ValueError("supporting identities must be an object")
    _exact_keys(value, _SUPPORTING_IDENTITY_KEYS, name="supporting identities")
    documents = value["source_documents"]
    if not isinstance(documents, Mapping):
        raise ValueError("source_documents must be an object")
    _exact_keys(documents, _SOURCE_DOCUMENT_KEYS, name="source_documents")
    for name, row in documents.items():
        if not isinstance(row, Mapping):
            raise ValueError(f"source_documents.{name} must be an object")
        _exact_keys(row, {"path", "complete_file_sha256"}, name=name)
        if not isinstance(row["path"], str) or not row["path"]:
            raise ValueError(f"{name}.path is invalid")
        _sha256(row["complete_file_sha256"], name=f"{name}.complete_file_sha256")
    _git_identity(value["theory_checkpoint"], name="theory_checkpoint")
    _git_identity(
        value["theory_erratum_checkpoint"],
        name="theory_erratum_checkpoint",
    )
    implementations = value["implementations"]
    _exact_keys(implementations, {"parent", "fork"}, name="implementations")
    _git_identity(implementations["parent"], name="implementations.parent")
    _git_identity(implementations["fork"], name="implementations.fork")
    environment = value["environment"]
    _exact_keys(environment, {"main_lock", "fork_lock"}, name="environment")
    for name, row in environment.items():
        _exact_keys(row, {"path", "complete_file_sha256"}, name=name)
        _sha256(row["complete_file_sha256"], name=f"{name}.complete_file_sha256")
    sdim = value["sdim"]
    _exact_keys(
        sdim,
        {
            "bootstrap",
            "runtime_inventory_schema",
            "state_sha256",
            "projection_sha256",
            "envelope_complete_file_sha256",
            "launch_receipt_complete_file_sha256",
        },
        name="sdim",
    )
    _exact_keys(
        sdim["bootstrap"],
        {"path", "complete_file_sha256"},
        name="sdim.bootstrap",
    )
    for key in (
        "state_sha256",
        "projection_sha256",
        "envelope_complete_file_sha256",
        "launch_receipt_complete_file_sha256",
    ):
        _sha256(sdim[key], name=f"sdim.{key}")
    manager = value["manager_preflight"]
    _exact_keys(
        manager,
        {
            "path",
            "schema",
            "result_projection_sha256",
            "byte_length",
            "complete_file_sha256",
            "security_projection",
        },
        name="manager_preflight",
    )
    _plain_int(manager["byte_length"], name="manager byte_length", minimum=1)
    _sha256(
        manager["result_projection_sha256"],
        name="manager result_projection_sha256",
    )
    _sha256(
        manager["complete_file_sha256"],
        name="manager complete_file_sha256",
    )
    if not isinstance(manager["security_projection"], Mapping):
        raise ValueError("manager security projection must be an object")
    schemas = value["result_schemas"]
    if not isinstance(schemas, Mapping) or not schemas:
        raise ValueError("result_schemas must be a nonempty object")
    if any(not isinstance(key, str) or not isinstance(item, str) for key, item in schemas.items()):
        raise ValueError("result_schemas must map strings to strings")
    mask = value["mask_contract"]
    _exact_keys(
        mask,
        {
            "namespace_version",
            "carrier_mask_index",
            "blpensemble_mask_indices",
            "probability_denominator",
            "structural_endpoints",
            "nested_probability_sweep",
        },
        name="mask_contract",
    )
    if (
        mask["namespace_version"] != "gcapeps-finite-memory-mask-v1"
        or mask["carrier_mask_index"] != 0
        or mask["blpensemble_mask_indices"] != list(range(32))
        or mask["probability_denominator"] != 4
        or mask["structural_endpoints"] is not True
        or mask["nested_probability_sweep"] is not True
    ):
        raise ValueError("event-mask binding drifted")
    _validate_json_value(value, name="supporting identities")


def _expected_heldout_cells(rounds_star: int) -> list[dict[str, Any]]:
    rounds_star = _plain_int(
        rounds_star, name="rounds_star", minimum=1
    )
    if rounds_star not in CALIBRATION_ROUNDS:
        raise ValueError("rounds_star is outside the calibration grid")
    memberships: dict[tuple[int, int, int, int, int], set[str]] = {}

    def add(cell: tuple[int, int, int, int, int], member: str) -> None:
        memberships.setdefault(cell, set()).add(member)

    for width in (3, 5, 7):
        add((width, rounds_star, 3, 3, 4), "width")
    for rounds in (1, 2, 4, rounds_star):
        add((7, rounds, 3, 3, 4), "rounds")
    for axis_family in (1, 2, 3):
        add((7, rounds_star, axis_family, 3, 4), "axis_family")
    for numerator in (0, 1, 2, 3, 4):
        add((7, rounds_star, 3, numerator, 4), "probability")
    order = ("width", "rounds", "axis_family", "probability")
    rows = []
    for cell in sorted(memberships):
        width, rounds, axis_family, numerator, denominator = cell
        membership = [name for name in order if name in memberships[cell]]
        rows.append(
            {
                "cell": list(cell),
                "case_id": (
                    f"heldout-w{width}-r{rounds}-a{axis_family}-"
                    f"p{numerator}of{denominator}"
                ),
                "slice_membership": membership,
                "run_blpensemble": "probability" in membership,
            }
        )
    expected_count = 11 if rounds_star == 4 else 12
    if len(rows) != expected_count:
        raise AssertionError("held-out cell cardinality drifted")
    return rows


def _validate_materialization(
    value: Mapping[str, Any],
    *,
    selection: Mapping[str, Any],
) -> None:
    _exact_keys(
        value,
        {
            "rounds_star",
            "gamma_index",
            "heldout_seed",
            "cell_list",
            "cell_list_sha256",
            "fixture_projection_sha256s",
            "fixtures",
            "heldout_fixture_sha256",
        },
        name="heldout materialization",
    )
    if (
        value["rounds_star"] != selection["rounds_star"]
        or value["gamma_index"] != selection["gamma_index"]
        or value["heldout_seed"] != HELDOUT_SEED
    ):
        raise ValueError("held-out materialization selection drifted")
    expected_cells = _expected_heldout_cells(selection["rounds_star"])
    if canonical_json_bytes(value["cell_list"]) != canonical_json_bytes(
        expected_cells
    ):
        raise ValueError("held-out materialization cell list drifted")
    if value["cell_list_sha256"] != canonical_sha256(expected_cells):
        raise ValueError("held-out cell-list SHA-256 mismatch")
    if (
        not isinstance(value["fixtures"], list)
        or not isinstance(value["fixture_projection_sha256s"], list)
        or len(value["fixtures"]) != len(expected_cells)
        or len(value["fixture_projection_sha256s"]) != len(expected_cells)
    ):
        raise ValueError("held-out fixture materialization cardinality drifted")
    for index, (fixture, digest) in enumerate(
        zip(value["fixtures"], value["fixture_projection_sha256s"], strict=True)
    ):
        if not isinstance(fixture, Mapping):
            raise ValueError(f"fixture {index} is not an object")
        _sha256(digest, name=f"fixture_projection_sha256s[{index}]")
        if fixture.get("result_projection_sha256") != digest:
            raise ValueError(f"fixture {index} projection binding drifted")
    unhashed = dict(value)
    digest = unhashed.pop("heldout_fixture_sha256")
    if digest != canonical_sha256(unhashed):
        raise ValueError("held-out materialization SHA-256 mismatch")


def build_target_amendment(
    *,
    calibration_report: Mapping[str, Any],
    calibration_publication_receipt: Mapping[str, Any],
    calibration_report_path: str,
    calibration_report_complete_file_sha256: str,
    calibration_publication_receipt_path: str,
    calibration_publication_receipt_complete_file_sha256: str,
    heldout_materialization: Mapping[str, Any],
    supporting_identities: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the tracked, self-commit-free target amendment."""

    validate_calibration_report(calibration_report)
    validate_calibration_publication_receipt(
        calibration_publication_receipt,
        report=calibration_report,
    )
    if (
        calibration_publication_receipt["final_calibration_class"]
        != CALIBRATION_PASS
        or calibration_publication_receipt["committed_by_deadline"] is not True
    ):
        raise ValueError("only timely PASS calibration can create an amendment")
    selection = calibration_report["selection"]
    _validate_selection(selection)
    validate_supporting_identities(supporting_identities)
    _validate_materialization(heldout_materialization, selection=selection)
    report_raw = canonical_json_bytes(calibration_report)
    receipt_raw = canonical_json_bytes(calibration_publication_receipt)
    if calibration_report_complete_file_sha256 != hashlib.sha256(
        report_raw
    ).hexdigest():
        raise ValueError("external calibration report hash drifted")
    if calibration_publication_receipt_complete_file_sha256 != hashlib.sha256(
        receipt_raw
    ).hexdigest():
        raise ValueError("external calibration receipt hash drifted")
    payload = {
        "schema": TARGET_AMENDMENT_SCHEMA,
        "calibration_report": {
            "path": calibration_report_path,
            "schema": CALIBRATION_SCHEMA,
            "result_projection_sha256": calibration_report[
                "result_projection_sha256"
            ],
            "byte_length": len(report_raw),
            "complete_file_sha256": calibration_report_complete_file_sha256,
        },
        "calibration_publication_receipt": {
            "path": calibration_publication_receipt_path,
            "schema": CALIBRATION_PUBLICATION_RECEIPT_SCHEMA,
            "result_projection_sha256": calibration_publication_receipt[
                "result_projection_sha256"
            ],
            "byte_length": len(receipt_raw),
            "complete_file_sha256": (
                calibration_publication_receipt_complete_file_sha256
            ),
        },
        "selection": dict(selection),
        "heldout": {
            "heldout_seed": HELDOUT_SEED,
            "registered_input_ids": [1, 2],
            "mask_namespaces": {
                "CARRIER": [0],
                "BLPENSEMBLE": list(range(32)),
            },
            "cell_list": heldout_materialization["cell_list"],
            "cell_list_sha256": heldout_materialization["cell_list_sha256"],
            "fixture_projection_sha256s": heldout_materialization[
                "fixture_projection_sha256s"
            ],
            "heldout_fixture_sha256": heldout_materialization[
                "heldout_fixture_sha256"
            ],
        },
        "supporting_identities": dict(supporting_identities),
        "self_commit_binding": False,
    }
    return _with_projection(payload)


def validate_target_amendment(value: Mapping[str, Any]) -> None:
    _exact_keys(
        value,
        {
            "schema",
            "calibration_report",
            "calibration_publication_receipt",
            "selection",
            "heldout",
            "supporting_identities",
            "self_commit_binding",
            "result_projection_sha256",
        },
        name="target amendment",
    )
    if value["schema"] != TARGET_AMENDMENT_SCHEMA:
        raise ValueError("target amendment schema drifted")
    if value["self_commit_binding"] is not False:
        raise ValueError("target amendment cannot bind its own containing commit")
    _validate_selection(value["selection"])
    for name, schema in (
        ("calibration_report", CALIBRATION_SCHEMA),
        (
            "calibration_publication_receipt",
            CALIBRATION_PUBLICATION_RECEIPT_SCHEMA,
        ),
    ):
        row = value[name]
        _exact_keys(
            row,
            {
                "path",
                "schema",
                "result_projection_sha256",
                "byte_length",
                "complete_file_sha256",
            },
            name=name,
        )
        if row["schema"] != schema:
            raise ValueError(f"{name} schema drifted")
        _plain_int(row["byte_length"], name=f"{name}.byte_length", minimum=1)
        _sha256(
            row["result_projection_sha256"],
            name=f"{name}.result_projection_sha256",
        )
        _sha256(
            row["complete_file_sha256"],
            name=f"{name}.complete_file_sha256",
        )
    heldout = value["heldout"]
    _exact_keys(
        heldout,
        {
            "heldout_seed",
            "registered_input_ids",
            "mask_namespaces",
            "cell_list",
            "cell_list_sha256",
            "fixture_projection_sha256s",
            "heldout_fixture_sha256",
        },
        name="amendment heldout",
    )
    if (
        heldout["heldout_seed"] != HELDOUT_SEED
        or heldout["registered_input_ids"] != [1, 2]
        or heldout["mask_namespaces"]
        != {"CARRIER": [0], "BLPENSEMBLE": list(range(32))}
    ):
        raise ValueError("amendment held-out identities drifted")
    expected = _expected_heldout_cells(value["selection"]["rounds_star"])
    if canonical_json_bytes(heldout["cell_list"]) != canonical_json_bytes(
        expected
    ):
        raise ValueError("amendment held-out cell list drifted")
    if heldout["cell_list_sha256"] != canonical_sha256(expected):
        raise ValueError("amendment held-out cell hash drifted")
    if (
        not isinstance(heldout["fixture_projection_sha256s"], list)
        or len(heldout["fixture_projection_sha256s"]) != len(expected)
    ):
        raise ValueError("amendment fixture projection list drifted")
    for index, digest in enumerate(heldout["fixture_projection_sha256s"]):
        _sha256(digest, name=f"fixture_projection_sha256s[{index}]")
    _sha256(
        heldout["heldout_fixture_sha256"],
        name="heldout_fixture_sha256",
    )
    validate_supporting_identities(value["supporting_identities"])
    _validate_projection(
        value,
        forbidden_self_keys=(
            "complete_file_sha256",
            "amendment_commit",
            "amendment_tree",
        ),
    )


@dataclass(frozen=True)
class AmendmentCheckpoint:
    commit: str
    tree: str
    amendment_file_sha256: str

    def validate(self) -> None:
        _git_identity(
            {"commit": self.commit, "tree": self.tree},
            name="amendment checkpoint",
        )
        _sha256(
            self.amendment_file_sha256,
            name="amendment_file_sha256",
        )


@dataclass(frozen=True)
class HeldoutCellPlan:
    cell_index: int
    cell: tuple[int, int, int, int, int]
    case_id: str
    slice_membership: tuple[str, ...]
    run_blpensemble: bool
    fixture_launch: LaunchSpec
    workflow_launches: tuple[LaunchSpec, ...]


def build_heldout_plan(
    amendment: Mapping[str, Any],
    *,
    checkpoint: AmendmentCheckpoint,
) -> tuple[HeldoutCellPlan, ...]:
    """Build the exact fixture prelude and 15-node serial graph per cell."""

    validate_target_amendment(amendment)
    checkpoint.validate()
    if checkpoint.amendment_file_sha256 != hashlib.sha256(
        canonical_json_bytes(amendment)
    ).hexdigest():
        raise ValueError("amendment checkpoint file SHA-256 mismatch")
    gamma_index = amendment["selection"]["gamma_index"]
    cells = amendment["heldout"]["cell_list"]
    plans: list[HeldoutCellPlan] = []
    global_ordinal = 0
    workflow_ordinal = 0
    for cell_index, row in enumerate(cells):
        cell = tuple(row["cell"])
        width, rounds, axis_family, numerator, denominator = cell
        case_id = row["case_id"]
        fixture_id = f"held-c{cell_index:02d}-fixture"
        fixture = _launch_spec(
            ordinal=global_ordinal,
            run_partition=HELDOUT,
            phase="FIXTURE",
            case_id=case_id,
            launch_id=fixture_id,
            role=NEUTRAL_FIXTURE_EMITTER,
            role_parameters={
                "width": width,
                "rounds": rounds,
                "axis_family": axis_family,
                "p_event_numerator": numerator,
                "p_event_denominator": denominator,
                "seed": HELDOUT_SEED,
                "gamma_index": gamma_index,
                "run_blpensemble": row["run_blpensemble"],
                "heldout_cell_index": cell_index,
            },
        )
        global_ordinal += 1
        workflow: list[LaunchSpec] = []

        def add(
            *,
            suffix: str,
            role: str,
            parameters: Mapping[str, Any],
            dependencies: Sequence[str],
        ) -> str:
            nonlocal global_ordinal, workflow_ordinal
            launch_id = f"held-c{cell_index:02d}-{suffix}"
            workflow.append(
                _launch_spec(
                    ordinal=global_ordinal,
                    run_partition=HELDOUT,
                    phase="WORKFLOW",
                    case_id=case_id,
                    launch_id=launch_id,
                    role=role,
                    role_parameters=parameters,
                    dependencies=dependencies,
                    workflow_ordinal=workflow_ordinal,
                )
            )
            global_ordinal += 1
            workflow_ordinal += 1
            return launch_id

        dense_id = add(
            suffix="dense",
            role=DENSE_REFERENCE,
            parameters={"heldout_cell_index": cell_index},
            dependencies=(fixture_id,),
        )
        evidence_ids: list[str] = []
        for lane, role in (
            ("plain", PLAIN_EVIDENCE),
            ("gc", GCAPEPS_EVIDENCE),
        ):
            for input_id in (1, 2):
                evidence_ids.append(
                    add(
                        suffix=f"{lane}-evidence-i{input_id}",
                        role=role,
                        parameters={
                            "heldout_cell_index": cell_index,
                            "input_id": input_id,
                        },
                        dependencies=(fixture_id,),
                    )
                )
        add(
            suffix="plain-warmup",
            role=PLAIN_PERFORMANCE,
            parameters={
                "heldout_cell_index": cell_index,
                "input_id": 1,
                "sample_kind": "warmup",
                "sample_index": None,
            },
            dependencies=(fixture_id,),
        )
        add(
            suffix="gc-warmup",
            role=GCAPEPS_PERFORMANCE,
            parameters={
                "heldout_cell_index": cell_index,
                "input_id": 1,
                "sample_kind": "warmup",
                "sample_index": None,
            },
            dependencies=(fixture_id,),
        )
        measured_order = (
            ("plain", PLAIN_PERFORMANCE, 0),
            ("gc", GCAPEPS_PERFORMANCE, 0),
            ("gc", GCAPEPS_PERFORMANCE, 1),
            ("plain", PLAIN_PERFORMANCE, 1),
            ("plain", PLAIN_PERFORMANCE, 2),
            ("gc", GCAPEPS_PERFORMANCE, 2),
        )
        for lane, role, sample_index in measured_order:
            add(
                suffix=f"{lane}-measured-{sample_index}",
                role=role,
                parameters={
                    "heldout_cell_index": cell_index,
                    "input_id": 1,
                    "sample_kind": "measured",
                    "sample_index": sample_index,
                },
                dependencies=(fixture_id,),
            )
        sdim_id = add(
            suffix="sdim",
            role=SDIM_COMPUTATION,
            parameters={"heldout_cell_index": cell_index},
            dependencies=(fixture_id,),
        )
        add(
            suffix="comparator",
            role=TERMINAL_COMPARATOR,
            parameters={"heldout_cell_index": cell_index},
            dependencies=(
                fixture_id,
                dense_id,
                *evidence_ids,
                sdim_id,
            ),
        )
        if len(workflow) != 15:
            raise AssertionError("held-out workflow cardinality drifted")
        plans.append(
            HeldoutCellPlan(
                cell_index=cell_index,
                cell=cell,
                case_id=case_id,
                slice_membership=tuple(row["slice_membership"]),
                run_blpensemble=row["run_blpensemble"],
                fixture_launch=fixture,
                workflow_launches=tuple(workflow),
            )
        )
    return tuple(plans)


@dataclass(frozen=True)
class HeldoutCellExecution:
    cell_index: int
    case_id: str
    fixture_audit: LaunchAudit
    workflow_audit: tuple[LaunchAudit, ...]
    workflow_status: str
    case_workflow_supervisor_wall_ns: int | None
    scientific_disposition: str
    timing_disposition: str


@dataclass(frozen=True)
class HeldoutExecutionResult:
    terminal_class: str
    cells: tuple[HeldoutCellExecution, ...]


def run_heldout_plan(
    plans: Sequence[HeldoutCellPlan],
    launch_one: Callable[[LaunchSpec], NodeObservation],
    *,
    clock_ns: Callable[[], int],
) -> HeldoutExecutionResult:
    """Run a fake or real finalized-node callback under frozen propagation."""

    plan = tuple(plans)
    invalid_halt = False
    any_scientific_censor = False
    cells: list[HeldoutCellExecution] = []

    def execute(spec: LaunchSpec) -> LaunchAudit:
        observation = launch_one(spec)
        if not isinstance(observation, NodeObservation):
            raise TypeError("launch callback returned the wrong observation type")
        observation.validate_for(spec)
        return LaunchAudit(
            spec=spec,
            executed=True,
            disposition=observation.terminal_kind,
            terminal_kind=observation.terminal_kind,
            qualifier=observation.qualifier,
            envelope_complete_file_sha256=(
                observation.envelope_complete_file_sha256
            ),
            launch_receipt_complete_file_sha256=(
                observation.launch_receipt_complete_file_sha256
            ),
        )

    for cell in plan:
        if invalid_halt:
            skipped_fixture = LaunchAudit(
                spec=cell.fixture_launch,
                executed=False,
                disposition="SKIPPED_INVALID_CONTROL",
                terminal_kind=None,
                qualifier=None,
                envelope_complete_file_sha256=None,
                launch_receipt_complete_file_sha256=None,
            )
            skipped = tuple(
                LaunchAudit(
                    spec=spec,
                    executed=False,
                    disposition="SKIPPED_INVALID_CONTROL",
                    terminal_kind=None,
                    qualifier=None,
                    envelope_complete_file_sha256=None,
                    launch_receipt_complete_file_sha256=None,
                )
                for spec in cell.workflow_launches
            )
            cells.append(
                HeldoutCellExecution(
                    cell_index=cell.cell_index,
                    case_id=cell.case_id,
                    fixture_audit=skipped_fixture,
                    workflow_audit=skipped,
                    workflow_status="not_started",
                    case_workflow_supervisor_wall_ns=None,
                    scientific_disposition=HELDOUT_INVALID,
                    timing_disposition="UNAVAILABLE",
                )
            )
            continue
        fixture_audit = execute(cell.fixture_launch)
        if fixture_audit.terminal_kind == "invalid_control":
            invalid_halt = True
            scientific = HELDOUT_INVALID
            workflow_rows = tuple(
                LaunchAudit(
                    spec=spec,
                    executed=False,
                    disposition="SKIPPED_INVALID_CONTROL",
                    terminal_kind=None,
                    qualifier=None,
                    envelope_complete_file_sha256=None,
                    launch_receipt_complete_file_sha256=None,
                )
                for spec in cell.workflow_launches
            )
            cells.append(
                HeldoutCellExecution(
                    cell_index=cell.cell_index,
                    case_id=cell.case_id,
                    fixture_audit=fixture_audit,
                    workflow_audit=workflow_rows,
                    workflow_status="not_started",
                    case_workflow_supervisor_wall_ns=None,
                    scientific_disposition=scientific,
                    timing_disposition="UNAVAILABLE",
                )
            )
            continue
        if fixture_audit.terminal_kind in {"worker_censor", "supervisor_censor"}:
            any_scientific_censor = True
            workflow_rows = tuple(
                LaunchAudit(
                    spec=spec,
                    executed=False,
                    disposition="SKIPPED_PREREQUISITE",
                    terminal_kind=None,
                    qualifier=None,
                    envelope_complete_file_sha256=None,
                    launch_receipt_complete_file_sha256=None,
                )
                for spec in cell.workflow_launches
            )
            cells.append(
                HeldoutCellExecution(
                    cell_index=cell.cell_index,
                    case_id=cell.case_id,
                    fixture_audit=fixture_audit,
                    workflow_audit=workflow_rows,
                    workflow_status="not_started",
                    case_workflow_supervisor_wall_ns=None,
                    scientific_disposition="INCOMPLETE_CENSORED",
                    timing_disposition="UNAVAILABLE",
                )
            )
            continue

        workflow_root = _plain_int(
            clock_ns(), name="case workflow root", minimum=0
        )
        workflow_rows: list[LaunchAudit] = []
        blocked = False
        cell_invalid = False
        performance_censored = False
        for spec in cell.workflow_launches:
            if blocked:
                workflow_rows.append(
                    LaunchAudit(
                        spec=spec,
                        executed=False,
                        disposition=(
                            "SKIPPED_INVALID_CONTROL"
                            if cell_invalid
                            else "SKIPPED_PREREQUISITE"
                        ),
                        terminal_kind=None,
                        qualifier=None,
                        envelope_complete_file_sha256=None,
                        launch_receipt_complete_file_sha256=None,
                    )
                )
                continue
            row = execute(spec)
            workflow_rows.append(row)
            if row.terminal_kind == "invalid_control":
                blocked = True
                cell_invalid = True
                invalid_halt = True
            elif row.terminal_kind in {"worker_censor", "supervisor_censor"}:
                if spec.role in PERFORMANCE_ROLES:
                    performance_censored = True
                else:
                    blocked = True
                    any_scientific_censor = True
        workflow_end = _plain_int(
            clock_ns(), name="case workflow end", minimum=workflow_root
        )
        if cell_invalid:
            scientific = HELDOUT_INVALID
        elif blocked:
            scientific = "INCOMPLETE_CENSORED"
        else:
            scientific = "COMPLETED"
        complete = all(row.executed for row in workflow_rows) and not blocked
        cells.append(
            HeldoutCellExecution(
                cell_index=cell.cell_index,
                case_id=cell.case_id,
                fixture_audit=fixture_audit,
                workflow_audit=tuple(workflow_rows),
                workflow_status="completed" if complete else "partial",
                case_workflow_supervisor_wall_ns=workflow_end - workflow_root,
                scientific_disposition=scientific,
                timing_disposition=(
                    "UNAVAILABLE" if performance_censored else "AVAILABLE"
                ),
            )
        )
    if invalid_halt:
        terminal = HELDOUT_INVALID
    elif any_scientific_censor:
        terminal = HELDOUT_INCOMPLETE
    else:
        terminal = HELDOUT_COMPLETE
    return HeldoutExecutionResult(terminal_class=terminal, cells=tuple(cells))


@dataclass(frozen=True)
class MeasuredTimingSample:
    lane: str
    sample_index: int
    algorithm_wall_ns: int
    algorithm_cpu_ns: int
    state_update_wall_ns: int
    state_update_cpu_ns: int
    supervisor_launch_wall_ns: int
    final_carrier_hash: str
    population_rows: tuple[tuple[Any, ...], ...]

    def validate(self) -> None:
        if self.lane not in {"plain", "gc"}:
            raise ValueError("timing lane must be plain or gc")
        _plain_int(
            self.sample_index,
            name="sample_index",
            minimum=0,
            maximum=2,
        )
        for name, value in (
            ("algorithm_wall_ns", self.algorithm_wall_ns),
            ("algorithm_cpu_ns", self.algorithm_cpu_ns),
            ("state_update_wall_ns", self.state_update_wall_ns),
            ("state_update_cpu_ns", self.state_update_cpu_ns),
            ("supervisor_launch_wall_ns", self.supervisor_launch_wall_ns),
        ):
            _plain_int(value, name=name, minimum=0)
        _sha256(self.final_carrier_hash, name="final_carrier_hash")
        keys: set[tuple[Any, ...]] = set()
        algorithm_rows = []
        state_rows = []
        for index, row in enumerate(self.population_rows):
            if not isinstance(row, tuple) or len(row) != 7:
                raise ValueError("timing population row has wrong arity")
            scope, round_index, operation_index, step_index, kind, wall, cpu = row
            if not isinstance(scope, str) or not scope:
                raise ValueError("timing population scope is invalid")
            if not isinstance(kind, str) or not kind:
                raise ValueError("timing population kind is invalid")
            for name, value in (
                ("round_index", round_index),
                ("operation_index", operation_index),
                ("step_index", step_index),
            ):
                if value is not None:
                    _plain_int(value, name=f"population[{index}].{name}", minimum=0)
            _plain_int(wall, name=f"population[{index}].wall", minimum=0)
            _plain_int(cpu, name=f"population[{index}].cpu", minimum=0)
            key = row[:5]
            if key in keys:
                raise ValueError("duplicate registered timing population key")
            keys.add(key)
            if scope == "candidate_algorithm_case_e2e":
                algorithm_rows.append(row)
            if scope == "physical_operation":
                state_rows.append(row)
        if len(algorithm_rows) != 1:
            raise ValueError("timing population lacks unique algorithm root")
        if (
            algorithm_rows[0][5] != self.algorithm_wall_ns
            or algorithm_rows[0][6] != self.algorithm_cpu_ns
            or sum(row[5] for row in state_rows) != self.state_update_wall_ns
            or sum(row[6] for row in state_rows) != self.state_update_cpu_ns
        ):
            raise ValueError("timing derived scope totals disagree with spans")


_PERFORMANCE_SPAN_KEYS = {
    "span_id",
    "parent_span_id",
    "scope",
    "lane",
    "case_id",
    "trajectory_id",
    "round_index",
    "operation_index",
    "step_index",
    "kind",
    "status",
    "wall_start_offset_ns",
    "wall_end_offset_ns",
    "wall_duration_ns",
    "cpu_start_offset_ns",
    "cpu_end_offset_ns",
    "cpu_duration_ns",
    "child_wall_ns",
    "child_cpu_ns",
    "unattributed_wall_ns",
    "unattributed_cpu_ns",
}


def _strict_json_object(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, child in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key {key!r}")
        value[key] = child
    return value


def _parse_canonical_object(raw: bytes, *, name: str) -> dict[str, Any]:
    if not isinstance(raw, bytes):
        raise TypeError(f"{name} must be bytes")
    try:
        value = json.loads(
            raw.decode("ascii"),
            object_pairs_hook=_strict_json_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"nonfinite JSON token {token}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{name} is not canonical JSON") from exc
    if not isinstance(value, dict) or canonical_json_bytes(value) != raw:
        raise ValueError(f"{name} is not canonical compact ASCII JSON")
    return value


def measured_timing_sample_from_trailer(
    *,
    core_bytes: bytes,
    trailer_bytes: bytes,
    lane: str,
    case_id: str,
    sample_index: int,
    supervisor_launch_wall_ns: int,
    final_carrier_hash: str,
) -> MeasuredTimingSample:
    """Derive registered totals from one hash-bound raw worker trailer."""

    if lane not in {"plain", "gc"}:
        raise ValueError("timing lane must be plain or gc")
    if not isinstance(case_id, str) or not case_id:
        raise ValueError("timing case_id is invalid")
    if not isinstance(core_bytes, bytes):
        raise TypeError("performance core frame must be bytes")
    trailer = _parse_canonical_object(trailer_bytes, name="performance trailer")
    _exact_keys(
        trailer,
        {
            "schema",
            "core_byte_length",
            "core_sha256",
            "ru_maxrss_raw",
            "ru_maxrss_units",
            "sample_scope",
            "timing",
        },
        name="performance trailer",
    )
    if (
        trailer["schema"] != TRAILER_SCHEMA
        or trailer["core_byte_length"] != len(core_bytes)
        or trailer["core_sha256"] != hashlib.sha256(core_bytes).hexdigest()
        or trailer["ru_maxrss_units"] != "KiB_on_linux"
        or trailer["sample_scope"] != "post_worker_root_pre_trailer"
    ):
        raise ValueError("performance trailer identity/hash binding failed")
    _plain_int(
        trailer["ru_maxrss_raw"],
        name="performance trailer ru_maxrss_raw",
        minimum=0,
    )
    timing = trailer["timing"]
    _exact_keys(
        timing,
        {"schema", "wall_clock", "cpu_clock", "spans"},
        name="performance timing",
    )
    if (
        timing["schema"] != TIMING_SCHEMA
        or timing["wall_clock"] != WALL_CLOCK
        or timing["cpu_clock"] != CPU_CLOCK
        or not isinstance(timing["spans"], list)
        or not timing["spans"]
    ):
        raise ValueError("performance timing identity failed")
    expected_lane = "plain" if lane == "plain" else "gcapeps"
    by_id: dict[str, Mapping[str, Any]] = {}
    children: dict[str, list[Mapping[str, Any]]] = {}
    roots = []
    for span in timing["spans"]:
        _exact_keys(span, _PERFORMANCE_SPAN_KEYS, name="performance span")
        span_id = span["span_id"]
        if not isinstance(span_id, str) or not span_id or span_id in by_id:
            raise ValueError("performance timing span id is invalid")
        by_id[span_id] = span
        if (
            span["lane"] != expected_lane
            or span["case_id"] != case_id
            or span["trajectory_id"] != "input1"
            or span["status"] != "completed"
        ):
            raise ValueError("performance timing span identity drifted")
        for field in (
            "wall_start_offset_ns",
            "wall_end_offset_ns",
            "wall_duration_ns",
            "cpu_start_offset_ns",
            "cpu_end_offset_ns",
            "cpu_duration_ns",
            "child_wall_ns",
            "child_cpu_ns",
            "unattributed_wall_ns",
            "unattributed_cpu_ns",
        ):
            _plain_int(span[field], name=f"{span_id}.{field}", minimum=0)
        if (
            span["wall_duration_ns"]
            != span["wall_end_offset_ns"] - span["wall_start_offset_ns"]
            or span["cpu_duration_ns"]
            != span["cpu_end_offset_ns"] - span["cpu_start_offset_ns"]
        ):
            raise ValueError("performance timing duration identity failed")
        for field in ("round_index", "operation_index", "step_index"):
            value = span[field]
            if value is not None:
                _plain_int(value, name=f"{span_id}.{field}", minimum=0)
    for span in timing["spans"]:
        parent_id = span["parent_span_id"]
        if parent_id is None:
            roots.append(span)
        else:
            if parent_id not in by_id:
                raise ValueError("performance timing parent is missing")
            parent = by_id[parent_id]
            if not (
                parent["wall_start_offset_ns"] <= span["wall_start_offset_ns"]
                and span["wall_end_offset_ns"] <= parent["wall_end_offset_ns"]
                and parent["cpu_start_offset_ns"] <= span["cpu_start_offset_ns"]
                and span["cpu_end_offset_ns"] <= parent["cpu_end_offset_ns"]
            ):
                raise ValueError("performance timing child escapes parent")
            children.setdefault(parent_id, []).append(span)
    if len(roots) != 1:
        raise ValueError("performance timing must have one root")
    root = roots[0]
    if (
        root["scope"] != "performance_worker_total"
        or root["kind"] != "worker"
        or root["parent_span_id"] is not None
    ):
        raise ValueError("performance timing root is misclassified")
    for parent_id, parent in by_id.items():
        direct = sorted(
            children.get(parent_id, []),
            key=lambda row: (
                row["wall_start_offset_ns"],
                row["wall_end_offset_ns"],
                row["span_id"],
            ),
        )
        for left, right in zip(direct, direct[1:]):
            if (
                left["wall_end_offset_ns"] > right["wall_start_offset_ns"]
                or left["cpu_end_offset_ns"] > right["cpu_start_offset_ns"]
            ):
                raise ValueError("performance timing siblings overlap")
        child_wall = sum(row["wall_duration_ns"] for row in direct)
        child_cpu = sum(row["cpu_duration_ns"] for row in direct)
        if (
            parent["child_wall_ns"] != child_wall
            or parent["child_cpu_ns"] != child_cpu
            or parent["wall_duration_ns"]
            != child_wall + parent["unattributed_wall_ns"]
            or parent["cpu_duration_ns"]
            != child_cpu + parent["unattributed_cpu_ns"]
        ):
            raise ValueError("performance timing child reconciliation failed")
    root_children = children.get(root["span_id"], [])
    if {
        (row["scope"], row["kind"]) for row in root_children
    } != {
        ("setup_and_gate_mask_materialization", "fixture_validation"),
        ("candidate_algorithm_case_e2e", "no_shadow_trajectory"),
        ("serialization", "core_encoding"),
    }:
        raise ValueError("performance timing root child roles drifted")
    algorithms = [
        row
        for row in root_children
        if row["scope"] == "candidate_algorithm_case_e2e"
    ]
    if len(algorithms) != 1:
        raise ValueError("performance timing lacks unique algorithm span")
    algorithm = algorithms[0]

    def is_algorithm_descendant(span: Mapping[str, Any]) -> bool:
        current = span
        seen = set()
        while current["parent_span_id"] is not None:
            parent_id = current["parent_span_id"]
            if parent_id in seen:
                raise ValueError("performance timing parent cycle")
            seen.add(parent_id)
            if parent_id == algorithm["span_id"]:
                return True
            current = by_id[parent_id]
        return span["span_id"] == algorithm["span_id"]

    population = [
        span for span in timing["spans"] if is_algorithm_descendant(span)
    ]
    allowed_scopes = {
        "candidate_algorithm_case_e2e",
        "candidate_initialization",
        "round",
        "physical_operation",
        "named_algorithm_substep",
    }
    if any(span["scope"] not in allowed_scopes for span in population):
        raise ValueError("performance timing contains an unregistered scope")
    allowed_plain_kinds = {"one_site_absorption", "capped_native_split"}
    allowed_gc_kinds = {
        "frame_composition",
        "signed_pullback",
        "route_planning",
        "exact_PEPO_lowering",
        "construction_validation",
        "compression_validation",
        "native_identity_compression",
        "candidate_commit",
    }
    physical_spans = []
    for span in population:
        scope = span["scope"]
        parent = (
            by_id[span["parent_span_id"]]
            if span["parent_span_id"] is not None
            else None
        )
        if scope == "candidate_algorithm_case_e2e":
            if span is not algorithm:
                raise ValueError("nested algorithm timing scope is forbidden")
        elif scope == "candidate_initialization":
            if (
                parent is not algorithm
                or span["kind"] != "candidate_initialization"
                or any(
                    span[field] is not None
                    for field in (
                        "round_index",
                        "operation_index",
                        "step_index",
                    )
                )
            ):
                raise ValueError("candidate initialization span is misclassified")
        elif scope == "round":
            if (
                parent is not algorithm
                or span["kind"] != "round"
                or span["round_index"] is None
                or span["operation_index"] is not None
                or span["step_index"] is not None
            ):
                raise ValueError("round span is misclassified")
        elif scope == "physical_operation":
            if (
                parent is None
                or parent["scope"] != "round"
                or span["round_index"] != parent["round_index"]
                or span["operation_index"] is None
                or span["step_index"] is not None
                or span["kind"] not in {"H", "S", "CX", "PAULI_ROTATION"}
            ):
                raise ValueError("physical-operation timing leaf is misclassified")
            physical_spans.append(span)
        else:
            kind = span["kind"]
            native_split = (
                lane == "gc"
                and kind.startswith("native_compression_split:")
                and kind.removeprefix("native_compression_split:").isdigit()
            )
            allowed = (
                kind in allowed_plain_kinds
                if lane == "plain"
                else kind in allowed_gc_kinds or native_split
            )
            parent_is_valid = (
                parent is not None
                and (
                    (
                        not native_split
                        and parent["scope"] == "physical_operation"
                    )
                    or (
                        native_split
                        and parent["scope"] == "named_algorithm_substep"
                        and parent["kind"]
                        == "native_identity_compression"
                    )
                )
            )
            if (
                not allowed
                or not parent_is_valid
                or span["round_index"] != parent["round_index"]
                or span["operation_index"] != parent["operation_index"]
                or span["step_index"] is None
            ):
                raise ValueError("named algorithm substep is misclassified")
    if not physical_spans:
        raise ValueError("performance timing contains no physical operations")
    population_rows = tuple(
        sorted(
            [(
                span["scope"],
                span["round_index"],
                span["operation_index"],
                span["step_index"],
                span["kind"],
                span["wall_duration_ns"],
                span["cpu_duration_ns"],
            )
            for span in population
        ], key=lambda row: (
            row[0],
            -1 if row[1] is None else row[1],
            -1 if row[2] is None else row[2],
            -1 if row[3] is None else row[3],
            row[4],
        ))
    )
    sample = MeasuredTimingSample(
        lane=lane,
        sample_index=sample_index,
        algorithm_wall_ns=algorithm["wall_duration_ns"],
        algorithm_cpu_ns=algorithm["cpu_duration_ns"],
        state_update_wall_ns=sum(
            row["wall_duration_ns"] for row in physical_spans
        ),
        state_update_cpu_ns=sum(
            row["cpu_duration_ns"] for row in physical_spans
        ),
        supervisor_launch_wall_ns=supervisor_launch_wall_ns,
        final_carrier_hash=final_carrier_hash,
        population_rows=population_rows,
    )
    sample.validate()
    return sample


def _summary(
    values: Sequence[int],
    *,
    require_positive: bool,
) -> dict[str, Any]:
    if len(values) != 3:
        raise ValueError("performance aggregate requires exactly three samples")
    minimum = 1 if require_positive else 0
    checked = [
        _plain_int(value, name="performance aggregate value", minimum=minimum)
        for value in values
    ]
    median = statistics.median(checked)
    mad = statistics.median(abs(value - median) for value in checked)
    return {
        "raw": checked,
        "median": median,
        "mad": mad,
        "minimum": min(checked),
        "maximum": max(checked),
    }


def _registered_ratio(
    numerator: float,
    denominator: float,
    *,
    name: str,
) -> tuple[float | None, dict[str, Any]]:
    if numerator <= 0 or denominator <= 0:
        return None, {
            "status": "UNAVAILABLE",
            "reason": f"{name}_has_nonpositive_registered_scope",
        }
    return numerator / denominator, {
        "status": "AVAILABLE",
        "reason": None,
    }


def aggregate_primary_timing(
    samples: Sequence[MeasuredTimingSample],
    *,
    plain_evidence_worker_wall_ns: int,
    gc_evidence_worker_wall_ns: int,
    plain_evidence_final_carrier_hash: str,
    gc_evidence_final_carrier_hash: str,
) -> dict[str, Any]:
    """Aggregate exact 3/3 trailer-derived samples without timing proxies."""

    rows = tuple(samples)
    if len(rows) != 6:
        raise ValueError("primary timing requires exactly six measured samples")
    by_lane: dict[str, dict[int, MeasuredTimingSample]] = {
        "plain": {},
        "gc": {},
    }
    for row in rows:
        row.validate()
        if row.sample_index in by_lane[row.lane]:
            raise ValueError("duplicate measured sample index")
        by_lane[row.lane][row.sample_index] = row
    if set(by_lane["plain"]) != {0, 1, 2} or set(by_lane["gc"]) != {0, 1, 2}:
        raise ValueError("each lane requires sample indices 0,1,2")
    evidence_hashes = {
        "plain": _sha256(
            plain_evidence_final_carrier_hash,
            name="plain_evidence_final_carrier_hash",
        ),
        "gc": _sha256(
            gc_evidence_final_carrier_hash,
            name="gc_evidence_final_carrier_hash",
        ),
    }
    for lane in ("plain", "gc"):
        if any(
            row.final_carrier_hash != evidence_hashes[lane]
            for row in by_lane[lane].values()
        ):
            raise ValueError("performance/evidence final-carrier hash mismatch")
    plain_evidence = _plain_int(
        plain_evidence_worker_wall_ns,
        name="plain_evidence_worker_wall_ns",
        minimum=0,
    )
    gc_evidence = _plain_int(
        gc_evidence_worker_wall_ns,
        name="gc_evidence_worker_wall_ns",
        minimum=0,
    )
    lane_summary: dict[str, Any] = {}
    population_summary: dict[str, list[dict[str, Any]]] = {}
    for lane in ("plain", "gc"):
        ordered = [by_lane[lane][index] for index in (0, 1, 2)]
        key_maps = [
            {row[:5]: row[5:] for row in sample.population_rows}
            for sample in ordered
        ]
        if not (set(key_maps[0]) == set(key_maps[1]) == set(key_maps[2])):
            raise ValueError("timing population key drifted across samples")
        population_summary[lane] = [
            {
                "scope": key[0],
                "round_index": key[1],
                "operation_index": key[2],
                "step_index": key[3],
                "kind": key[4],
                "wall_ns": _summary(
                    [mapping[key][0] for mapping in key_maps],
                    require_positive=False,
                ),
                "cpu_ns": _summary(
                    [mapping[key][1] for mapping in key_maps],
                    require_positive=False,
                ),
            }
            for key in sorted(
                key_maps[0],
                key=lambda row: (
                    row[0],
                    -1 if row[1] is None else row[1],
                    -1 if row[2] is None else row[2],
                    -1 if row[3] is None else row[3],
                    row[4],
                ),
            )
        ]
        lane_summary[lane] = {
            "candidate_algorithm_case_e2e_wall_ns": _summary(
                [row.algorithm_wall_ns for row in ordered],
                require_positive=False,
            ),
            "candidate_algorithm_case_e2e_cpu_ns": _summary(
                [row.algorithm_cpu_ns for row in ordered],
                require_positive=False,
            ),
            "state_update_only_wall_ns": _summary(
                [row.state_update_wall_ns for row in ordered],
                require_positive=False,
            ),
            "state_update_only_cpu_ns": _summary(
                [row.state_update_cpu_ns for row in ordered],
                require_positive=False,
            ),
            "supervisor_launch_wall_ns": _summary(
                [row.supervisor_launch_wall_ns for row in ordered],
                require_positive=False,
            ),
            "measured_final_carrier_hashes": [
                row.final_carrier_hash for row in ordered
            ],
            "evidence_final_carrier_hash": evidence_hashes[lane],
        }
    wall_ratio, wall_status = _registered_ratio(
        lane_summary["gc"]["candidate_algorithm_case_e2e_wall_ns"]["median"],
        lane_summary["plain"]["candidate_algorithm_case_e2e_wall_ns"]["median"],
        name="candidate_algorithm_wall",
    )
    cpu_ratio, cpu_status = _registered_ratio(
        lane_summary["gc"]["candidate_algorithm_case_e2e_cpu_ns"]["median"],
        lane_summary["plain"]["candidate_algorithm_case_e2e_cpu_ns"]["median"],
        name="candidate_algorithm_cpu",
    )
    launch_ratio, launch_status = _registered_ratio(
        lane_summary["gc"]["supervisor_launch_wall_ns"]["median"],
        lane_summary["plain"]["supervisor_launch_wall_ns"]["median"],
        name="supervisor_launch_wall",
    )
    evidence_ratio, evidence_status = _registered_ratio(
        gc_evidence,
        plain_evidence,
        name="evidence_worker_wall",
    )
    if wall_ratio is None:
        band = "UNAVAILABLE"
    elif wall_ratio < 0.80:
        band = "GC_FASTER"
    elif wall_ratio <= 1.25:
        band = "SAME_ORDER"
    else:
        band = "GC_OVERHEAD"
    return {
        "population": {
            "trajectory_id": 1,
            "sample_kind": "measured",
            "sample_indices": [0, 1, 2],
            "ratio_direction": "gc_over_plain",
        },
        "lanes": lane_summary,
        "registered_population_aggregates": population_summary,
        "singleton_evidence_worker_wall_ns": {
            "plain": plain_evidence,
            "gc": gc_evidence,
        },
        "ratios": {
            "candidate_algorithm_wall_gc_over_plain": wall_ratio,
            "candidate_algorithm_cpu_gc_over_plain": cpu_ratio,
            "supervisor_launch_wall_gc_over_plain": launch_ratio,
            "evidence_worker_wall_gc_over_plain": evidence_ratio,
        },
        "ratio_dispositions": {
            "candidate_algorithm_wall_gc_over_plain": wall_status,
            "candidate_algorithm_cpu_gc_over_plain": cpu_status,
            "supervisor_launch_wall_gc_over_plain": launch_status,
            "evidence_worker_wall_gc_over_plain": evidence_status,
        },
        "state_update_only_is_report_only_no_registered_ratio": True,
        "primary_wall_band": band,
    }


def classify_terminal_cell_science(
    *,
    amendment: Mapping[str, Any],
    cell_index: int,
    comparator_terminal_kind: str,
    comparator_core: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Classify one cell without reading any candidate-worker truth."""

    validate_target_amendment(amendment)
    index = _plain_int(
        cell_index,
        name="cell_index",
        minimum=0,
        maximum=len(amendment["heldout"]["cell_list"]) - 1,
    )
    cell_row = amendment["heldout"]["cell_list"][index]
    case_id = cell_row["case_id"]
    if comparator_terminal_kind == "invalid_control":
        if comparator_core is not None:
            raise ValueError("invalid comparator terminal cannot carry a core")
        scientific_class = HELDOUT_INVALID
        evidence = None
    elif comparator_terminal_kind in {"worker_censor", "supervisor_censor"}:
        if comparator_core is not None:
            raise ValueError("censored comparator terminal cannot carry a core")
        scientific_class = "INCOMPLETE_CENSORED"
        evidence = None
    elif comparator_terminal_kind == "completed_result":
        if not isinstance(comparator_core, Mapping):
            raise ValueError("completed comparator terminal requires its core")
        fixture_identity = comparator_core.get("fixture_identity")
        witness = comparator_core.get("exact_dense_memory_witnesses")
        if not isinstance(fixture_identity, Mapping) or not isinstance(
            witness, Mapping
        ):
            raise ValueError("comparator omitted registered scientific evidence")
        width, rounds, _axis_family, numerator, _denominator = cell_row["cell"]
        if (
            fixture_identity.get("run_partition") != HELDOUT
            or fixture_identity.get("case_id") != case_id
            or fixture_identity.get("width") != width
            or fixture_identity.get("rounds") != rounds
        ):
            raise ValueError("comparator fixture identity disagrees with amendment")
        _exact_keys(
            witness,
            {
                "fixed_blp",
                "finite_32_mask_ensemble_blp",
                "p_event_zero_control",
                "trajectory1_entanglement",
            },
            name="exact dense memory witnesses",
        )
        fixed = witness["fixed_blp"]
        if (
            not isinstance(fixed, Mapping)
            or fixed.get("object") != "fixed_carrier_mask"
            or fixed.get("witness_threshold") != 1.0e-10
            or fixed.get("verdict")
            not in {
                "BLP_WITNESSED_FIXED_MASK",
                "NO_WITNESS_FIXED_MASK_FOR_REGISTERED_PAIR",
            }
        ):
            raise ValueError("fixed-mask BLP terminal evidence is invalid")
        ensemble = witness["finite_32_mask_ensemble_blp"]
        if cell_row["run_blpensemble"]:
            if (
                not isinstance(ensemble, Mapping)
                or ensemble.get("object") != "finite_32_mask_ensemble"
                or ensemble.get("witness_threshold") != 1.0e-10
                or ensemble.get("verdict")
                not in {
                    "BLP_WITNESSED_FINITE_32_MASK_ENSEMBLE",
                    (
                        "NO_WITNESS_FINITE_32_MASK_ENSEMBLE_"
                        "FOR_REGISTERED_PAIR"
                    ),
                }
            ):
                raise ValueError("finite-32 BLP terminal evidence is invalid")
        elif ensemble is not None:
            raise ValueError("non-probability cell claimed finite-32 BLP")
        control = witness["p_event_zero_control"]
        if numerator == 0:
            if not isinstance(control, Mapping) or control.get("passed") is not True:
                raise ValueError("p_event=0 terminal control did not pass")
        elif control is not None:
            raise ValueError("nonzero-p cell emitted p_event=0 control")
        entropy = witness["trajectory1_entanglement"]
        required_entropy = {
            "source",
            "candidate_values_consumed",
            "round_indices",
            "entropy_von_neumann",
            "entropy_renyi2",
            "normalized_schmidt_values_by_round",
            "numerical_schmidt_rank_by_round",
            "entropy_von_neumann_increments",
            "negative_increment_rows",
            "revival_rows",
            "maximum_entropy_von_neumann",
            "terminal_entropy_von_neumann",
            "round1_entropy_von_neumann",
            "terminal_minus_round1",
            "h_e_strict_threshold",
            "h_e_condition_holds",
            "conditional_h_e_verdict_if_amendment_bound_stress_cell",
            "h_e_applicability_deferred_to_amendment_bound_stress_cell",
        }
        _exact_keys(entropy, required_entropy, name="trajectory1 entropy")
        s1 = entropy["entropy_von_neumann"]
        if (
            entropy["source"] != "exact_dense_fixed_carrier_input1"
            or entropy["candidate_values_consumed"] is not False
            or entropy["round_indices"] != list(range(rounds + 1))
            or not isinstance(s1, list)
            or len(s1) != rounds + 1
            or entropy["h_e_strict_threshold"] != 1.0e-10
            or entropy[
                "h_e_applicability_deferred_to_amendment_bound_stress_cell"
            ]
            is not True
        ):
            raise ValueError("trajectory1 entropy identity is invalid")
        checked_s1 = [
            float(_finite_number)
            for _finite_number in (
                _finite_float(value, name="entropy_von_neumann")
                for value in s1
            )
        ]
        increments = [
            float(checked_s1[round_index] - checked_s1[round_index - 1])
            for round_index in range(1, rounds + 1)
        ]
        delta = float(checked_s1[-1] - checked_s1[1])
        if (
            entropy["entropy_von_neumann_increments"] != increments
            or entropy["terminal_entropy_von_neumann"] != checked_s1[-1]
            or entropy["round1_entropy_von_neumann"] != checked_s1[1]
            or entropy["terminal_minus_round1"] != delta
            or entropy["maximum_entropy_von_neumann"] != max(checked_s1)
            or entropy["h_e_condition_holds"] is not (delta > 1.0e-10)
            or entropy[
                "conditional_h_e_verdict_if_amendment_bound_stress_cell"
            ]
            != ("supported" if delta > 1.0e-10 else "falsified")
        ):
            raise ValueError("trajectory1 entropy derived fields are corrupted")
        stress_cell = (
            7,
            amendment["selection"]["rounds_star"],
            3,
            3,
            4,
        )
        applicable = tuple(cell_row["cell"]) == stress_cell
        h_e = {
            "applicable_only_to_registered_stress_cell": applicable,
            "stress_cell": list(stress_cell),
            "terminal_minus_round1": delta,
            "strict_threshold": 1.0e-10,
            "verdict": (
                entropy[
                    "conditional_h_e_verdict_if_amendment_bound_stress_cell"
                ]
                if applicable
                else "DESCRIPTIVE_NOT_APPLICABLE"
            ),
            "verdict_owner": "terminal_comparator",
            "monotonic_step_claim": False,
        }
        faithfulness = comparator_core.get("final_bond32_faithfulness")
        positive_gate = comparator_core.get("positive_bond32_gate")
        if not isinstance(faithfulness, Mapping) or not isinstance(
            positive_gate, Mapping
        ):
            raise ValueError("comparator omitted registered H_F evidence")
        _exact_keys(
            faithfulness,
            {
                "round_index",
                "delta_f",
                "per_path_class",
                "shared_positive_truncation_eligible",
                "conditional_h_f_verdict_if_amendment_bound_stress_cell",
                "h_f_applicability_deferred_to_amendment_bound_stress_cell",
            },
            name="final bond-32 faithfulness",
        )
        delta_f = faithfulness["delta_f"]
        if not isinstance(delta_f, Mapping):
            raise TypeError("final bond-32 delta_f must be an object")
        _exact_keys(
            delta_f,
            {
                "minimum_plain_fidelity",
                "minimum_gcapeps_fidelity",
                "delta_fidelity",
                "tie_tolerance",
                "direction",
            },
            name="final bond-32 delta_f",
        )
        minimum_plain = _finite_float(
            delta_f["minimum_plain_fidelity"],
            name="minimum plain fidelity",
        )
        minimum_gc = _finite_float(
            delta_f["minimum_gcapeps_fidelity"],
            name="minimum GCAPEPS fidelity",
        )
        delta_f_value = float(minimum_gc - minimum_plain)
        if not (0.0 <= minimum_plain <= 1.0 and 0.0 <= minimum_gc <= 1.0):
            raise ValueError("minimum stress fidelity is outside [0,1]")
        expected_direction = (
            "gcapeps_higher"
            if delta_f_value > 1.0e-10
            else "plain_higher"
            if delta_f_value < -1.0e-10
            else "tie"
        )
        shared_positive = faithfulness[
            "shared_positive_truncation_eligible"
        ]
        gate_shared_positive = positive_gate.get("all_four_paths_positive")
        if (
            faithfulness["round_index"] != rounds
            or faithfulness[
                "h_f_applicability_deferred_to_amendment_bound_stress_cell"
            ]
            is not True
            or not isinstance(shared_positive, bool)
            or not isinstance(gate_shared_positive, bool)
            or shared_positive is not gate_shared_positive
            or delta_f["tie_tolerance"] != 1.0e-10
            or delta_f["delta_fidelity"] != delta_f_value
            or delta_f["direction"] != expected_direction
        ):
            raise ValueError("final bond-32 H_F evidence is inconsistent")
        expected_conditional_h_f = (
            "INELIGIBLE_NO_SHARED_POSITIVE_TRUNCATION"
            if not shared_positive
            else "supported"
            if expected_direction == "gcapeps_higher"
            else "falsified"
            if expected_direction == "plain_higher"
            else "tie/inconclusive"
        )
        if faithfulness[
            "conditional_h_f_verdict_if_amendment_bound_stress_cell"
        ] != expected_conditional_h_f:
            raise ValueError("conditional comparator H_F verdict is corrupted")
        h_f = {
            "applicable_only_to_registered_stress_cell": applicable,
            "stress_cell": list(stress_cell),
            "delta_fidelity": delta_f_value,
            "tie_tolerance": 1.0e-10,
            "shared_positive_truncation_eligible": shared_positive,
            "verdict": (
                faithfulness[
                    "conditional_h_f_verdict_if_amendment_bound_stress_cell"
                ]
                if applicable
                else "DESCRIPTIVE_NOT_APPLICABLE"
            ),
            "verdict_owner": "terminal_comparator",
            "source": "terminal_comparator_complete_state_metrics",
        }
        scientific_class = "COMPLETED"
        evidence = {
            "fixed_blp_verdict": fixed["verdict"],
            "finite_32_mask_ensemble_blp_verdict": (
                None if ensemble is None else ensemble["verdict"]
            ),
            "p_event_zero_control": control,
            "h_e": h_e,
            "h_f": h_f,
        }
    else:
        raise ValueError("unregistered comparator terminal kind")
    payload = {
        "schema": TERMINAL_CELL_ACCEPTANCE_SCHEMA,
        "cell_index": index,
        "case_id": case_id,
        "comparator_terminal_kind": comparator_terminal_kind,
        "scientific_class": scientific_class,
        "evaluator_source": "terminal_comparator_exact_dense_projection",
        "candidate_worker_truth_consumed_for_blp_or_h_e": False,
        "scientific_evidence": evidence,
    }
    return _with_projection(payload)


def build_heldout_report(
    *,
    amendment: Mapping[str, Any],
    checkpoint: AmendmentCheckpoint,
    execution: HeldoutExecutionResult,
    cell_results: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the raw terminal aggregate without a self complete-file digest."""

    validate_target_amendment(amendment)
    checkpoint.validate()
    if checkpoint.amendment_file_sha256 != hashlib.sha256(
        canonical_json_bytes(amendment)
    ).hexdigest():
        raise ValueError("held-out report amendment hash mismatch")
    _validate_json_value(cell_results, name="cell_results")
    complete_workflows = [
        row.case_workflow_supervisor_wall_ns
        for row in execution.cells
        if row.workflow_status == "completed"
    ]
    payload = {
        "schema": HELDOUT_REPORT_SCHEMA,
        "run_partition": HELDOUT,
        "terminal_class": execution.terminal_class,
        "amendment_checkpoint": {
            "commit": checkpoint.commit,
            "tree": checkpoint.tree,
            "amendment_file_sha256": checkpoint.amendment_file_sha256,
        },
        "amendment_result_projection_sha256": amendment[
            "result_projection_sha256"
        ],
        "cell_list_sha256": amendment["heldout"]["cell_list_sha256"],
        "cells": [
            {
                "cell_index": row.cell_index,
                "case_id": row.case_id,
                "fixture": _launch_audit_json(row.fixture_audit),
                "workflow": [
                    _launch_audit_json(audit) for audit in row.workflow_audit
                ],
                "workflow_status": row.workflow_status,
                "case_workflow_supervisor_wall_ns": (
                    row.case_workflow_supervisor_wall_ns
                ),
                "scientific_disposition": row.scientific_disposition,
                "timing_disposition": row.timing_disposition,
            }
            for row in execution.cells
        ],
        "complete_case_workflow_supervisor_wall_ns": complete_workflows,
        "partial_workflows_excluded_from_aggregate": True,
        "cell_results": dict(cell_results),
        "claim_boundary": (
            "bounded pure-state persistent-memory carrier comparison only; "
            "not a QEC Record, generic PEPS certificate, monotonic-memory "
            "theorem, or universal GCAPEPS speedup"
        ),
    }
    return _with_projection(payload)


def validate_heldout_report(
    value: Mapping[str, Any],
    *,
    amendment: Mapping[str, Any],
) -> None:
    validate_target_amendment(amendment)
    _exact_keys(
        value,
        {
            "schema",
            "run_partition",
            "terminal_class",
            "amendment_checkpoint",
            "amendment_result_projection_sha256",
            "cell_list_sha256",
            "cells",
            "complete_case_workflow_supervisor_wall_ns",
            "partial_workflows_excluded_from_aggregate",
            "cell_results",
            "claim_boundary",
            "result_projection_sha256",
        },
        name="held-out report",
    )
    if (
        value["schema"] != HELDOUT_REPORT_SCHEMA
        or value["run_partition"] != HELDOUT
        or value["terminal_class"]
        not in {HELDOUT_COMPLETE, HELDOUT_INCOMPLETE, HELDOUT_INVALID}
    ):
        raise ValueError("held-out report identity drifted")
    _git_identity(
        {
            "commit": value["amendment_checkpoint"]["commit"],
            "tree": value["amendment_checkpoint"]["tree"],
        },
        name="held-out amendment checkpoint",
    )
    _sha256(
        value["amendment_checkpoint"]["amendment_file_sha256"],
        name="held-out amendment file hash",
    )
    if (
        value["amendment_result_projection_sha256"]
        != amendment["result_projection_sha256"]
        or value["cell_list_sha256"]
        != amendment["heldout"]["cell_list_sha256"]
        or value["partial_workflows_excluded_from_aggregate"] is not True
    ):
        raise ValueError("held-out report amendment/aggregation binding drifted")
    complete_from_cells = [
        row["case_workflow_supervisor_wall_ns"]
        for row in value["cells"]
        if row["workflow_status"] == "completed"
    ]
    if value["complete_case_workflow_supervisor_wall_ns"] != complete_from_cells:
        raise ValueError("partial workflow leaked into complete aggregate")
    _validate_projection(
        value,
        forbidden_self_keys=(
            "complete_file_sha256",
            "heldout_report_complete_file_sha256",
        ),
    )
