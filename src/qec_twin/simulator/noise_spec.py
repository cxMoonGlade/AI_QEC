from __future__ import annotations

"""Noise specifications for the simulator frontend.

This block is intentionally limited to Stim-representable Pauli noise. Analog
joint-Lindbladian, source-coupled, coherent non-Clifford, and leakage noise will
use separate truth sidecars and backend adapters; they are not encoded here.
"""

from dataclasses import dataclass
import math
from typing import Literal

import numpy as np

from qec_twin.mechanisms.source_process import SourceTimeline
from qec_twin.simulator.circuit_ir import CircuitIR, CircuitStep, GateOp, MeasureOp, Tick
from qec_twin.simulator.source_sidecar import SourceTimelineBinding

SOURCE_PROJECTION_AUDIT_METADATA_KEY = "_source_projection_evaluator_audit"


_ONE_QUBIT_UNITARIES = {
    "H",
    "I",
    "X",
    "Y",
    "Z",
    "S",
    "S_DAG",
    "SQRT_X",
    "SQRT_X_DAG",
    "SQRT_Y",
    "SQRT_Y_DAG",
    "SQRT_Z",
    "SQRT_Z_DAG",
}

_TWO_QUBIT_UNITARIES = {
    "CX",
    "CY",
    "CZ",
    "ISWAP",
    "ISWAP_DAG",
    "SQRT_XX",
    "SQRT_XX_DAG",
    "SQRT_YY",
    "SQRT_YY_DAG",
    "SQRT_ZZ",
    "SQRT_ZZ_DAG",
    "SWAP",
    "XCX",
    "XCY",
    "XCZ",
    "YCX",
    "YCY",
    "YCZ",
}
_Z_MEASUREMENTS = {"M", "MR", "MZ", "MRZ"}
_MEASUREMENTS = _Z_MEASUREMENTS | {"MX", "MY", "MRX", "MRY"}
_NOISE_INSTRUCTIONS = {
    "DEPOLARIZE1",
    "DEPOLARIZE2",
    "X_ERROR",
    "Y_ERROR",
    "Z_ERROR",
}
_AUTO_DEPOLARIZE_ALIASES = {"DEPOLARIZE", "DEPOLARIZING"}


@dataclass(frozen=True)
class StimPauliNoiseSpec:
    """Stim-compatible Pauli/depolarizing projection.

    `after_1q_depolarization` inserts `DEPOLARIZE1(p)` after 1q unitary gates.
    `after_2q_depolarization` inserts `DEPOLARIZE2(p)` after 2q unitary gates.
    `before_measure_flip` inserts `X_ERROR(p)` immediately before Z-basis
    measurements. Non-Z measurement flips are deliberately not guessed.
    """

    after_1q_depolarization: float = 0.0
    after_2q_depolarization: float = 0.0
    before_measure_flip: float = 0.0

    def __post_init__(self) -> None:
        for name, value in (
            ("after_1q_depolarization", self.after_1q_depolarization),
            ("after_2q_depolarization", self.after_2q_depolarization),
            ("before_measure_flip", self.before_measure_flip),
        ):
            object.__setattr__(self, name, _validate_probability(name, value))

    @property
    def is_trivial(self) -> bool:
        return (
            self.after_1q_depolarization == 0.0
            and self.after_2q_depolarization == 0.0
            and self.before_measure_flip == 0.0
        )

    def to_manifest(self) -> dict:
        return {
            "type": "stim_pauli",
            "after_1q_depolarization": float(self.after_1q_depolarization),
            "after_2q_depolarization": float(self.after_2q_depolarization),
            "before_measure_flip": float(self.before_measure_flip),
        }


@dataclass(frozen=True)
class StimNoiseRule:
    """One explicit Stim-representable noise placement rule.

    `position` is `after` for gates, `before` for measurements, and `during`
    for implicit idles ending at a `TICK` boundary.
    `match_kind` selects one gate occurrence, one instruction name, all gates, one
    measurement instruction name, or idle qubits. Gate occurrence indices count
    user non-noise `GateOp`s in the original `CircuitIR`, starting at zero.
    For gate/measurement rules, `target_filter` is an exact instruction-target
    tuple filter. It is never an inserted-target override: inserted noise always
    lands on the matched operation targets. To address one pair/qubit inside a
    bundled instruction, split that source instruction first. For idle rules,
    `target_filter` selects the candidate idle qubits at `TICK` boundaries.
    """

    position: str
    match_kind: str
    noise: str
    args: tuple[float, ...]
    gate_index: int | None = None
    gate_name: str | None = None
    measure_name: str | None = None
    target_filter: tuple[int, ...] | None = None
    require_match: bool = True

    def __post_init__(self) -> None:
        position = str(self.position).lower()
        match_kind = str(self.match_kind).lower()
        if position not in {"after", "before", "during"}:
            raise ValueError(
                f"noise rule position must be 'after', 'before', or 'during', got {self.position!r}"
            )
        if match_kind not in {"gate_index", "gate_type", "all_gates", "measurement_type", "idle"}:
            raise ValueError(f"unsupported noise rule match_kind {self.match_kind!r}")
        if position == "before" and match_kind != "measurement_type":
            raise ValueError("before rules currently support measurement_type only")
        if position == "after" and match_kind == "measurement_type":
            raise ValueError("measurement_type rules must use position='before'")
        if position == "during" and match_kind != "idle":
            raise ValueError("during rules currently support idle only")
        if match_kind == "idle" and position != "during":
            raise ValueError("idle rules must use position='during'")
        noise = str(self.noise).upper()
        args = tuple(_validate_probability("noise probability", a) for a in self.args)
        object.__setattr__(self, "position", position)
        object.__setattr__(self, "match_kind", match_kind)
        object.__setattr__(self, "noise", noise)
        object.__setattr__(self, "args", args)
        object.__setattr__(self, "gate_name", None if self.gate_name is None else str(self.gate_name).upper())
        object.__setattr__(
            self,
            "measure_name",
            None if self.measure_name is None else str(self.measure_name).upper(),
        )
        if self.match_kind == "gate_index":
            object.__setattr__(
                self,
                "gate_index",
                _strict_nonnegative_int("gate_index", self.gate_index),
            )
        if self.match_kind == "gate_type" and not self.gate_name:
            raise ValueError("gate_type rules require gate_name")
        if self.match_kind == "measurement_type" and not self.measure_name:
            raise ValueError("measurement_type rules require measure_name")
        if noise not in _NOISE_INSTRUCTIONS and noise not in _AUTO_DEPOLARIZE_ALIASES:
            raise ValueError(
                "targeted frontend noise currently supports X_ERROR/Y_ERROR/Z_ERROR, "
                "DEPOLARIZE/DEPOLARIZING, DEPOLARIZE1, and DEPOLARIZE2 only; "
                f"got {noise!r}"
            )
        if match_kind == "idle" and noise == "DEPOLARIZE2":
            raise ValueError("idle noise is per-qubit in this frontend slice; use DEPOLARIZE/DEPOLARIZE1")
        if len(args) != 1:
            raise ValueError(f"{noise} rules require exactly one probability argument, got {len(args)}")
        filt = None if self.target_filter is None else tuple(int(t) for t in self.target_filter)
        object.__setattr__(self, "target_filter", filt)

    def to_manifest(self) -> dict:
        return {
            "position": self.position,
            "match_kind": self.match_kind,
            "noise": self.noise,
            "args": list(self.args),
            "gate_index": self.gate_index,
            "gate_name": self.gate_name,
            "measure_name": self.measure_name,
            "target_filter": None if self.target_filter is None else list(self.target_filter),
            "require_match": bool(self.require_match),
        }


@dataclass(frozen=True)
class TargetedStimNoiseSpec:
    """Ordered, location-aware Stim noise insertion rules."""

    rules: tuple[StimNoiseRule, ...]
    schema: str = "qec_twin.simulator.TargetedStimNoiseSpec.v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "rules", tuple(self.rules))

    @property
    def is_trivial(self) -> bool:
        return not self.rules

    def to_manifest(self) -> dict:
        return {
            "type": "targeted_stim_pauli",
            "schema": self.schema,
            "rules": [rule.to_manifest() for rule in self.rules],
        }


@dataclass(frozen=True)
class SourceStimPauliRule:
    """One source-conditioned reduced Pauli projection rule.

    This is an executable Stim-Pauli projection, not analog source truth. The
    source payload is converted to one probability per matched operation/cycle.
    """

    position: str
    match_kind: str
    noise: str
    payload_key: str = "z_radns"
    map_kind: Literal["logit", "payload_probability"] = "logit"
    base_p: float = 1.0e-3
    sensitivity: float = 1.0
    z_scale: float = 1.0e-4
    gate_index: int | None = None
    gate_name: str | None = None
    measure_name: str | None = None
    target_filter: tuple[int, ...] | None = None
    require_match: bool = True

    def __post_init__(self) -> None:
        if self.map_kind not in {"logit", "payload_probability"}:
            raise ValueError("map_kind must be 'logit' or 'payload_probability'")
        base_p = _validate_probability("base_p", self.base_p)
        if self.map_kind == "logit" and base_p <= 0.0:
            raise ValueError("logit source projection requires base_p > 0")
        sensitivity = float(self.sensitivity)
        if not math.isfinite(sensitivity):
            raise ValueError(f"sensitivity must be finite, got {self.sensitivity!r}")
        z_scale = float(self.z_scale)
        if not math.isfinite(z_scale) or z_scale <= 0.0:
            raise ValueError(f"z_scale must be finite and > 0, got {self.z_scale!r}")
        target_filter = _strict_optional_targets("target_filter", self.target_filter)
        probe = StimNoiseRule(
            position=self.position,
            match_kind=self.match_kind,
            noise=self.noise,
            args=(base_p,),
            gate_index=self.gate_index,
            gate_name=self.gate_name,
            measure_name=self.measure_name,
            target_filter=target_filter,
            require_match=self.require_match,
        )
        object.__setattr__(self, "position", probe.position)
        object.__setattr__(self, "match_kind", probe.match_kind)
        object.__setattr__(self, "noise", probe.noise)
        object.__setattr__(self, "base_p", base_p)
        object.__setattr__(self, "sensitivity", sensitivity)
        object.__setattr__(self, "z_scale", z_scale)
        object.__setattr__(self, "gate_index", probe.gate_index)
        object.__setattr__(self, "gate_name", probe.gate_name)
        object.__setattr__(self, "measure_name", probe.measure_name)
        object.__setattr__(self, "target_filter", probe.target_filter)
        object.__setattr__(self, "payload_key", str(self.payload_key))

    def probability_for(
        self,
        timeline: SourceTimeline,
        *,
        cycle_index: int,
        targets: tuple[int, ...],
    ) -> float:
        payload = timeline.payload_series(self.payload_key)
        if cycle_index < 0 or cycle_index >= payload.shape[0]:
            raise IndexError(f"cycle_index={cycle_index} outside source timeline length {payload.shape[0]}")
        value = _payload_value_for_targets(payload, cycle_index=cycle_index, targets=targets)
        if self.map_kind == "payload_probability":
            return _validate_probability(f"{self.payload_key}[{cycle_index}]", value)
        x = float(value) / float(self.z_scale)
        logit = math.log(float(self.base_p) / (1.0 - float(self.base_p)))
        y = max(-60.0, min(60.0, logit + float(self.sensitivity) * x))
        return _validate_probability("source-projected probability", 1.0 / (1.0 + math.exp(-y)))

    def to_public_manifest(self) -> dict:
        return {
            "position": self.position,
            "match_kind": self.match_kind,
            "noise": self.noise,
            "gate_index": self.gate_index,
            "gate_name": self.gate_name,
            "measure_name": self.measure_name,
            "target_filter": None if self.target_filter is None else list(self.target_filter),
            "require_match": bool(self.require_match),
            "probability_source": "evaluator_only_source_projection_binding",
        }

    def to_manifest(self) -> dict:
        return {
            "position": self.position,
            "match_kind": self.match_kind,
            "noise": self.noise,
            "payload_key": self.payload_key,
            "map_kind": self.map_kind,
            "base_p": float(self.base_p),
            "sensitivity": float(self.sensitivity),
            "z_scale": float(self.z_scale),
            "gate_index": self.gate_index,
            "gate_name": self.gate_name,
            "measure_name": self.measure_name,
            "target_filter": None if self.target_filter is None else list(self.target_filter),
            "require_match": bool(self.require_match),
        }


@dataclass(frozen=True)
class SourceStimPauliProjectionSpec:
    """Executable reduced Pauli projection conditioned on a SourceTimeline.

    The exact source is evaluator-only sidecar truth. The projected noisy Stim
    circuit contains only the resulting Pauli probabilities.
    """

    timeline: SourceTimeline
    rules: tuple[SourceStimPauliRule, ...]
    source_binding: SourceTimelineBinding | None = None
    schema: str = "qec_twin.simulator.SourceStimPauliProjectionSpec.v1"

    def __post_init__(self) -> None:
        rules = tuple(self.rules)
        object.__setattr__(self, "rules", rules)
        if not self.rules:
            raise ValueError("SourceStimPauliProjectionSpec requires at least one rule")
        payload_keys = tuple(sorted({rule.payload_key for rule in rules}))
        missing_payloads = [key for key in payload_keys if key not in self.timeline.payload]
        if missing_payloads:
            raise KeyError(f"source projection payload key(s) missing from timeline: {missing_payloads!r}")
        binding = self.source_binding or SourceTimelineBinding(
            cycle_binding="circuit_tick",
            payload_keys=payload_keys,
        )
        if binding.cycle_binding != "circuit_tick":
            raise NotImplementedError(
                "SourceStimPauliProjectionSpec currently executes source cycles as CircuitIR TICK "
                "indices; use source_binding=SourceTimelineBinding(cycle_binding='circuit_tick')"
            )
        if binding.payload_keys:
            omitted = set(payload_keys) - set(binding.payload_keys)
            if omitted:
                raise ValueError(
                    "source projection binding payload_keys omit rule payload key(s): "
                    f"{sorted(omitted)!r}"
                )
        object.__setattr__(self, "source_binding", binding)

    @property
    def is_trivial(self) -> bool:
        return False

    @property
    def source_timeline(self) -> SourceTimeline:
        return self.timeline

    def to_manifest(self) -> dict:
        return {
            "type": "stim_pauli_source_projection",
            "schema": self.schema,
            "visibility": "reduced_public_summary",
            "representability": "reduced_pauli_projection_not_analog_truth",
            "source": {
                "sidecar_required": True,
                "cycle_binding": self.source_binding.cycle_binding if self.source_binding else None,
                "n_cycles": int(self.timeline.n_cycles),
                "cycle_time_ns": float(self.timeline.cycle_time_ns),
            },
            "rules": [rule.to_public_manifest() for rule in self.rules],
            "boundary": (
                "Executable frontend projection into Stim Pauli noise. This is not "
                "joint-Lindbladian, coherent, leakage, or full analog source truth."
            ),
        }

    def to_evaluator_manifest(self) -> dict:
        return {
            "type": "stim_pauli_source_projection",
            "schema": self.schema,
            "visibility": "evaluator_only",
            "representability": "reduced_pauli_projection_not_analog_truth",
            "source_cycle_map": "CircuitIR TICK index; cycle 0 is before the first TICK",
            "source_timeline": {
                "name": self.timeline.name,
                "schema": self.timeline.schema,
                "n_cycles": int(self.timeline.n_cycles),
                "cycle_time_ns": float(self.timeline.cycle_time_ns),
                "coupling_mode": self.timeline.coupling_mode,
            },
            "rules": [rule.to_manifest() for rule in self.rules],
            "execution_status": _source_projection_execution_status(),
        }


class NoiseBuilder:
    """Fluent builder for user-facing Stim-representable noise placement."""

    def __init__(self) -> None:
        self._rules: list[StimNoiseRule] = []

    def after_gate(
        self,
        gate_index: int,
        noise: str,
        p: float,
        *,
        target_filter: int | tuple[int, ...] | list[int] | None = None,
        require_match: bool = True,
    ) -> "NoiseBuilder":
        self._rules.append(
            StimNoiseRule(
                position="after",
                match_kind="gate_index",
                gate_index=gate_index,
                noise=str(noise),
                args=(float(p),),
                target_filter=_optional_targets(target_filter),
                require_match=bool(require_match),
            )
        )
        return self

    def after_gate_type(
        self,
        gate: str,
        noise: str,
        p: float,
        *,
        target_filter: int | tuple[int, ...] | list[int] | None = None,
        require_match: bool = True,
    ) -> "NoiseBuilder":
        self._rules.append(
            StimNoiseRule(
                position="after",
                match_kind="gate_type",
                gate_name=str(gate),
                noise=str(noise),
                args=(float(p),),
                target_filter=_optional_targets(target_filter),
                require_match=bool(require_match),
            )
        )
        return self

    def after_all_gates(
        self,
        noise: str,
        p: float,
        *,
        target_filter: int | tuple[int, ...] | list[int] | None = None,
        require_match: bool = True,
    ) -> "NoiseBuilder":
        self._rules.append(
            StimNoiseRule(
                position="after",
                match_kind="all_gates",
                noise=str(noise),
                args=(float(p),),
                target_filter=_optional_targets(target_filter),
                require_match=bool(require_match),
            )
        )
        return self

    def before_measurement(
        self,
        noise: str,
        p: float,
        *,
        basis: str = "Z",
        target_filter: int | tuple[int, ...] | list[int] | None = None,
        require_match: bool = True,
    ) -> "NoiseBuilder":
        basis = str(basis).upper()
        if basis not in {"X", "Y", "Z"}:
            raise ValueError(f"measurement basis must be X, Y, or Z, got {basis!r}")
        self._rules.append(
            StimNoiseRule(
                position="before",
                match_kind="measurement_type",
                measure_name="M" if basis == "Z" else f"M{basis}",
                noise=str(noise),
                args=(float(p),),
                target_filter=_optional_targets(target_filter),
                require_match=bool(require_match),
            )
        )
        return self

    def before_measurement_type(
        self,
        measurement: str,
        noise: str,
        p: float,
        *,
        target_filter: int | tuple[int, ...] | list[int] | None = None,
        require_match: bool = True,
    ) -> "NoiseBuilder":
        self._rules.append(
            StimNoiseRule(
                position="before",
                match_kind="measurement_type",
                measure_name=str(measurement),
                noise=str(noise),
                args=(float(p),),
                target_filter=_optional_targets(target_filter),
                require_match=bool(require_match),
            )
        )
        return self

    def during_idle(
        self,
        noise: str,
        p: float,
        *,
        targets: int | tuple[int, ...] | list[int] | None = None,
        require_match: bool = True,
    ) -> "NoiseBuilder":
        self._rules.append(
            StimNoiseRule(
                position="during",
                match_kind="idle",
                noise=str(noise),
                args=(float(p),),
                target_filter=_optional_targets(targets),
                require_match=bool(require_match),
            )
        )
        return self

    def build(self) -> TargetedStimNoiseSpec:
        return TargetedStimNoiseSpec(tuple(self._rules))


FrontendNoiseSpec = StimPauliNoiseSpec | TargetedStimNoiseSpec | SourceStimPauliProjectionSpec


def apply_stim_pauli_noise(circuit: CircuitIR, noise: FrontendNoiseSpec | None) -> CircuitIR:
    """Return a new CircuitIR with Stim-compatible noise instructions inserted."""

    if noise is None or noise.is_trivial:
        return circuit
    if isinstance(noise, SourceStimPauliProjectionSpec):
        return _apply_source_stim_pauli_projection(circuit, noise)
    if isinstance(noise, TargetedStimNoiseSpec):
        return _apply_targeted_stim_noise(circuit, noise)
    steps: list[CircuitStep] = []
    for step in circuit.steps:
        if isinstance(step, MeasureOp) and noise.before_measure_flip > 0.0:
            if step.name not in _Z_MEASUREMENTS:
                raise NotImplementedError(
                    f"before_measure_flip currently supports Z-basis measurements only, got {step.name}"
                )
            steps.append(GateOp("X_ERROR", step.targets, (float(noise.before_measure_flip),)))
            steps.append(step)
            continue
        steps.append(step)
        if isinstance(step, GateOp):
            if step.name in _ONE_QUBIT_UNITARIES and noise.after_1q_depolarization > 0.0:
                steps.append(
                    GateOp("DEPOLARIZE1", step.targets, (float(noise.after_1q_depolarization),))
                )
            elif step.name in _TWO_QUBIT_UNITARIES and noise.after_2q_depolarization > 0.0:
                steps.append(
                    GateOp("DEPOLARIZE2", step.targets, (float(noise.after_2q_depolarization),))
                )
    metadata = dict(circuit.metadata)
    metadata["noise_projection"] = noise.to_manifest()
    return CircuitIR(
        num_qubits=circuit.num_qubits,
        steps=tuple(steps),
        metadata=metadata,
        _allow_noise_steps=True,
    )


def _apply_source_stim_pauli_projection(circuit: CircuitIR, noise: SourceStimPauliProjectionSpec) -> CircuitIR:
    steps: list[CircuitStep] = []
    matched = [0 for _ in noise.rules]
    skipped_outside_timeline = [0 for _ in noise.rules]
    matched_events: list[list[dict]] = [[] for _ in noise.rules]
    gate_index = 0
    tick_index = 0
    active_touched: set[int] = set()
    for step in circuit.steps:
        if isinstance(step, Tick):
            _append_source_idle_noise(
                steps,
                circuit.num_qubits,
                active_touched,
                noise,
                matched,
                skipped_outside_timeline,
                matched_events,
                tick_index=tick_index,
            )
            active_touched.clear()
            steps.append(step)
            tick_index += 1
            continue

        if isinstance(step, MeasureOp):
            for i, rule in enumerate(noise.rules):
                if rule.position == "before" and _source_rule_matches_measurement(rule, step):
                    _append_source_noise_if_in_timeline(
                        steps,
                        noise,
                        rule,
                        i,
                        step.targets,
                        matched,
                        skipped_outside_timeline,
                        matched_events,
                        matched_step=step,
                        gate_index=None,
                        tick_index=tick_index,
                    )
            steps.append(step)
            active_touched.update(step.targets)
            continue

        steps.append(step)
        if isinstance(step, GateOp) and step.name not in _NOISE_INSTRUCTIONS:
            for i, rule in enumerate(noise.rules):
                if rule.position == "after" and _source_rule_matches_gate(rule, step, gate_index):
                    _append_source_noise_if_in_timeline(
                        steps,
                        noise,
                        rule,
                        i,
                        step.targets,
                        matched,
                        skipped_outside_timeline,
                        matched_events,
                        matched_step=step,
                        gate_index=gate_index,
                        tick_index=tick_index,
                    )
            if step.name != "I":
                active_touched.update(step.targets)
            gate_index += 1

    missing = [
        _source_rule_label(i, rule)
        for i, (rule, count) in enumerate(zip(noise.rules, matched, strict=True))
        if rule.require_match and count == 0
    ]
    missing.extend(
        _source_rule_label(i, rule)
        for i, (rule, skipped) in enumerate(zip(noise.rules, skipped_outside_timeline, strict=True))
        if rule.require_match and skipped > 0
    )
    if missing:
        raise ValueError(
            "source projection rule(s) were not fully covered by the source timeline: "
            f"{missing}"
        )

    metadata = dict(circuit.metadata)
    manifest = noise.to_manifest()
    manifest["matched_counts"] = matched
    manifest["skipped_outside_timeline"] = skipped_outside_timeline
    manifest["matched_event_counts"] = [len(events) for events in matched_events]
    audit = noise.to_evaluator_manifest()
    audit["matched_counts"] = matched
    audit["skipped_outside_timeline"] = skipped_outside_timeline
    audit["matched_events"] = matched_events
    metadata["noise_projection"] = manifest
    metadata[SOURCE_PROJECTION_AUDIT_METADATA_KEY] = audit
    return CircuitIR(
        num_qubits=circuit.num_qubits,
        steps=tuple(steps),
        metadata=metadata,
        _allow_noise_steps=True,
    )


def _append_source_idle_noise(
    steps: list[CircuitStep],
    num_qubits: int,
    active_touched: set[int],
    noise: SourceStimPauliProjectionSpec,
    matched: list[int],
    skipped_outside_timeline: list[int],
    matched_events: list[list[dict]],
    *,
    tick_index: int,
) -> None:
    for i, rule in enumerate(noise.rules):
        if rule.position != "during" or rule.match_kind != "idle":
            continue
        candidates = set(range(int(num_qubits))) if rule.target_filter is None else set(rule.target_filter)
        idle_targets = tuple(sorted(candidates.difference(active_touched)))
        if not idle_targets:
            continue
        _append_source_noise_if_in_timeline(
            steps,
            noise,
            rule,
            i,
            idle_targets,
            matched,
            skipped_outside_timeline,
            matched_events,
            matched_step=None,
            gate_index=None,
            tick_index=tick_index,
        )


def _apply_targeted_stim_noise(circuit: CircuitIR, noise: TargetedStimNoiseSpec) -> CircuitIR:
    steps: list[CircuitStep] = []
    matched = [0 for _ in noise.rules]
    matched_events: list[list[dict]] = [[] for _ in noise.rules]
    gate_index = 0
    tick_index = 0
    active_touched: set[int] = set()
    for step in circuit.steps:
        if isinstance(step, Tick):
            _append_idle_noise(
                steps,
                circuit.num_qubits,
                active_touched,
                noise,
                matched,
                matched_events,
                tick_index=tick_index,
            )
            active_touched.clear()
            steps.append(step)
            tick_index += 1
            continue

        if isinstance(step, MeasureOp):
            for i, rule in enumerate(noise.rules):
                if rule.position == "before" and _rule_matches_measurement(rule, step):
                    noise_step = _noise_gate_for_rule(rule, step.targets, matched_step=step)
                    steps.append(noise_step)
                    matched[i] += 1
                    matched_events[i].append(
                        _match_event(
                            rule,
                            matched_step=step,
                            noise_step=noise_step,
                            gate_index=None,
                            tick_index=tick_index,
                        )
                    )
            steps.append(step)
            active_touched.update(step.targets)
            continue

        steps.append(step)
        if isinstance(step, GateOp) and step.name not in _NOISE_INSTRUCTIONS:
            for i, rule in enumerate(noise.rules):
                if rule.position == "after" and _rule_matches_gate(rule, step, gate_index):
                    noise_step = _noise_gate_for_rule(rule, step.targets, matched_step=step)
                    steps.append(noise_step)
                    matched[i] += 1
                    matched_events[i].append(
                        _match_event(
                            rule,
                            matched_step=step,
                            noise_step=noise_step,
                            gate_index=gate_index,
                            tick_index=tick_index,
                        )
                    )
            if step.name != "I":
                active_touched.update(step.targets)
            gate_index += 1

    missing = [
        _rule_label(i, rule)
        for i, (rule, count) in enumerate(zip(noise.rules, matched, strict=True))
        if rule.require_match and count == 0
    ]
    if missing:
        raise ValueError(f"targeted noise rule(s) matched no circuit operation: {missing}")

    metadata = dict(circuit.metadata)
    manifest = noise.to_manifest()
    manifest["matched_counts"] = matched
    manifest["matched_events"] = matched_events
    metadata["noise_projection"] = manifest
    return CircuitIR(
        num_qubits=circuit.num_qubits,
        steps=tuple(steps),
        metadata=metadata,
        _allow_noise_steps=True,
    )


def _append_idle_noise(
    steps: list[CircuitStep],
    num_qubits: int,
    active_touched: set[int],
    noise: TargetedStimNoiseSpec,
    matched: list[int],
    matched_events: list[list[dict]],
    *,
    tick_index: int,
) -> None:
    for i, rule in enumerate(noise.rules):
        if rule.position != "during" or rule.match_kind != "idle":
            continue
        candidates = set(range(int(num_qubits))) if rule.target_filter is None else set(rule.target_filter)
        idle_targets = tuple(sorted(candidates.difference(active_touched)))
        if not idle_targets:
            continue
        name = _resolve_idle_noise_name(rule.noise)
        _validate_noise_targets(name, idle_targets)
        noise_step = GateOp(name, idle_targets, rule.args)
        steps.append(noise_step)
        matched[i] += 1
        matched_events[i].append(
            {
                "position": "during",
                "match_kind": "idle",
                "tick_index": int(tick_index),
                "active_touched": sorted(int(q) for q in active_touched),
                "idle_targets": list(idle_targets),
                "noise": noise_step.name,
                "noise_targets": list(noise_step.targets),
            }
        )


def _append_source_noise_if_in_timeline(
    steps: list[CircuitStep],
    noise: SourceStimPauliProjectionSpec,
    rule: SourceStimPauliRule,
    rule_index: int,
    targets: tuple[int, ...],
    matched: list[int],
    skipped_outside_timeline: list[int],
    matched_events: list[list[dict]],
    *,
    matched_step: GateOp | MeasureOp | None,
    gate_index: int | None,
    tick_index: int,
) -> None:
    if tick_index >= noise.timeline.n_cycles:
        skipped_outside_timeline[rule_index] += 1
        return
    if rule.match_kind == "idle":
        name = _resolve_idle_noise_name(rule.noise)
    else:
        probe = _source_rule_as_stim_rule(rule, rule.base_p)
        if matched_step is None:  # pragma: no cover - guarded by match_kind
            raise ValueError("matched_step is required for non-idle source projection")
        name = _resolve_noise_name(probe.noise, matched_step)
    for group_targets, site_reduction in _source_noise_target_groups(
        noise.timeline,
        rule,
        name=name,
        targets=targets,
    ):
        projected_p = rule.probability_for(
            noise.timeline,
            cycle_index=tick_index,
            targets=group_targets,
        )
        _validate_noise_targets(name, group_targets)
        noise_step = GateOp(name, group_targets, (projected_p,))
        steps.append(noise_step)
        matched[rule_index] += 1
        matched_events[rule_index].append(
            _source_match_event(
                rule,
                noise_step=noise_step,
                matched_step=matched_step,
                gate_index=gate_index,
                tick_index=tick_index,
                targets=group_targets,
                site_reduction=site_reduction,
            )
        )


def _source_rule_matches_gate(rule: SourceStimPauliRule, step: GateOp, gate_index: int) -> bool:
    return _rule_matches_gate(_source_rule_as_stim_rule(rule, rule.base_p), step, gate_index)


def _source_rule_matches_measurement(rule: SourceStimPauliRule, step: MeasureOp) -> bool:
    return _rule_matches_measurement(_source_rule_as_stim_rule(rule, rule.base_p), step)


def _source_rule_as_stim_rule(rule: SourceStimPauliRule, p: float) -> StimNoiseRule:
    return StimNoiseRule(
        position=rule.position,
        match_kind=rule.match_kind,
        noise=rule.noise,
        args=(_validate_probability("source-projected probability", p),),
        gate_index=rule.gate_index,
        gate_name=rule.gate_name,
        measure_name=rule.measure_name,
        target_filter=rule.target_filter,
        require_match=rule.require_match,
    )


def _source_match_event(
    rule: SourceStimPauliRule,
    *,
    noise_step: GateOp,
    matched_step: GateOp | MeasureOp | None,
    gate_index: int | None,
    tick_index: int,
    targets: tuple[int, ...],
    site_reduction: str,
) -> dict:
    event = {
        "position": rule.position,
        "match_kind": rule.match_kind,
        "noise": noise_step.name,
        "noise_targets": list(noise_step.targets),
        "tick_index": int(tick_index),
        "source_cycle": int(tick_index),
        "source_cycle_binding": "circuit_tick",
        "projected_probability": float(noise_step.args[0]),
        "payload_key": rule.payload_key,
        "site_reduction": site_reduction,
    }
    if matched_step is None:
        event["matched_op"] = "IDLE"
        event["matched_targets"] = list(targets)
    else:
        event["matched_op"] = matched_step.name
        event["matched_targets"] = list(matched_step.targets)
    if gate_index is not None:
        event["gate_index"] = int(gate_index)
    return event


def _source_rule_label(index: int, rule: SourceStimPauliRule) -> str:
    key = rule.gate_index if rule.gate_index is not None else rule.gate_name or rule.measure_name or "idle"
    return f"source_rule[{index}] {rule.match_kind}:{key}"


def _payload_value_for_targets(
    payload: np.ndarray,
    *,
    cycle_index: int,
    targets: tuple[int, ...],
) -> float:
    arr = np.asarray(payload, dtype=np.float64)
    if arr.ndim == 1:
        return float(arr[cycle_index])
    if arr.ndim == 2:
        if targets:
            if min(targets) < 0 or max(targets) >= arr.shape[1]:
                raise ValueError(
                    f"source payload has {arr.shape[1]} sites but matched targets were {targets}"
                )
            return float(np.mean(arr[cycle_index, list(targets)]))
        return float(np.mean(arr[cycle_index]))
    raise ValueError(f"source payload must be 1-D or 2-D, got shape {arr.shape}")


def _source_noise_target_groups(
    timeline: SourceTimeline,
    rule: SourceStimPauliRule,
    *,
    name: str,
    targets: tuple[int, ...],
) -> tuple[tuple[tuple[int, ...], str], ...]:
    payload = np.asarray(timeline.payload_series(rule.payload_key))
    if payload.ndim != 2:
        return ((targets, "global_cycle_payload"),)
    if not targets:
        return ((targets, "empty_target_error"),)
    if name == "DEPOLARIZE2":
        _validate_noise_targets(name, targets)
        return tuple(
            (tuple(targets[i : i + 2]), "per_pair_mean_from_site_payload")
            for i in range(0, len(targets), 2)
        )
    return tuple(((int(target),), "per_target_from_site_payload") for target in targets)


def _rule_matches_gate(rule: StimNoiseRule, step: GateOp, gate_index: int) -> bool:
    if rule.target_filter is not None and tuple(step.targets) != tuple(rule.target_filter):
        return False
    if rule.match_kind == "gate_index":
        return int(rule.gate_index) == int(gate_index)
    if rule.match_kind == "gate_type":
        return step.name == rule.gate_name
    if rule.match_kind == "all_gates":
        return True
    return False


def _rule_matches_measurement(rule: StimNoiseRule, step: MeasureOp) -> bool:
    if rule.match_kind != "measurement_type":
        return False
    if rule.target_filter is not None and tuple(step.targets) != tuple(rule.target_filter):
        return False
    if step.name == rule.measure_name:
        return True
    if rule.measure_name == "M" and step.name in {"M", "MZ", "MR", "MRZ"}:
        return True
    if rule.measure_name == "MX" and step.name in {"MX", "MRX"}:
        return True
    if rule.measure_name == "MY" and step.name in {"MY", "MRY"}:
        return True
    return False


def _noise_gate_for_rule(
    rule: StimNoiseRule,
    default_targets: tuple[int, ...],
    *,
    matched_step: GateOp | MeasureOp,
) -> GateOp:
    targets = default_targets
    name = _resolve_noise_name(rule.noise, matched_step)
    _validate_noise_targets(name, targets)
    return GateOp(name, targets, rule.args)


def _resolve_noise_name(noise: str, matched_step: GateOp | MeasureOp) -> str:
    if noise not in _AUTO_DEPOLARIZE_ALIASES:
        return noise
    if isinstance(matched_step, MeasureOp):
        raise ValueError("automatic DEPOLARIZE noise is only defined after gates, not before measurements")
    arity = _gate_arity(matched_step)
    if arity == 1:
        return "DEPOLARIZE1"
    if arity == 2:
        return "DEPOLARIZE2"
    raise ValueError(f"cannot auto-resolve DEPOLARIZE for gate {matched_step.name!r}")


def _resolve_idle_noise_name(noise: str) -> str:
    if noise in _AUTO_DEPOLARIZE_ALIASES:
        return "DEPOLARIZE1"
    if noise == "DEPOLARIZE2":
        raise ValueError("idle noise is per-qubit in this frontend slice; use DEPOLARIZE/DEPOLARIZE1")
    return noise


def _validate_noise_targets(name: str, targets: tuple[int, ...]) -> None:
    if not targets:
        raise ValueError(f"{name} requires at least one target")
    if name in {"X_ERROR", "Y_ERROR", "Z_ERROR", "DEPOLARIZE1"}:
        return
    if name == "DEPOLARIZE2":
        if len(targets) < 2 or len(targets) % 2:
            raise ValueError(f"DEPOLARIZE2 requires an even number of targets, got {targets}")
        return
    raise ValueError(f"unsupported frontend noise instruction {name!r}")


def _match_event(
    rule: StimNoiseRule,
    *,
    matched_step: GateOp | MeasureOp,
    noise_step: GateOp,
    gate_index: int | None,
    tick_index: int,
) -> dict:
    event = {
        "position": rule.position,
        "match_kind": rule.match_kind,
        "matched_op": matched_step.name,
        "matched_targets": list(matched_step.targets),
        "noise": noise_step.name,
        "noise_targets": list(noise_step.targets),
        "tick_index": int(tick_index),
    }
    if gate_index is not None:
        event["gate_index"] = int(gate_index)
    return event


def _rule_label(index: int, rule: StimNoiseRule) -> str:
    key = rule.gate_index if rule.gate_index is not None else rule.gate_name or rule.measure_name or "idle"
    return f"rule[{index}] {rule.match_kind}:{key}"


def _gate_arity(step: GateOp) -> int | None:
    if step.name in _ONE_QUBIT_UNITARIES or step.name in {"R", "RX", "RY", "RZ"}:
        return 1
    if step.name in _TWO_QUBIT_UNITARIES:
        return 2
    return None


def _optional_targets(targets: int | tuple[int, ...] | list[int] | None) -> tuple[int, ...] | None:
    if targets is None:
        return None
    if isinstance(targets, int):
        return (int(targets),)
    return tuple(int(t) for t in targets)


def _strict_optional_targets(
    name: str,
    targets: int | tuple[int, ...] | list[int] | None,
) -> tuple[int, ...] | None:
    if targets is None:
        return None
    if isinstance(targets, (int, np.integer)) and not isinstance(targets, bool):
        return (int(targets),)
    if isinstance(targets, (str, bytes)):
        raise ValueError(f"{name} must contain integer targets, not a string")
    out: list[int] = []
    for target in targets:
        if not isinstance(target, (int, np.integer)) or isinstance(target, bool):
            raise ValueError(f"{name} must contain integer targets, got {target!r}")
        out.append(int(target))
    return tuple(out)


def _strict_nonnegative_int(name: str, value: int | None) -> int:
    if value is None:
        raise ValueError(f"{name} rules require a non-negative integer {name}")
    if not isinstance(value, (int, np.integer)) or isinstance(value, bool):
        raise ValueError(f"{name} rules require a non-negative integer {name}, got {value!r}")
    out = int(value)
    if out < 0:
        raise ValueError(f"{name} rules require a non-negative integer {name}, got {value!r}")
    return out


def _validate_probability(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value < 1.0:
        raise ValueError(f"{name} must be in [0, 1), got {value!r}")
    return value


def _source_projection_execution_status() -> dict:
    return {
        "applied_to_stim_records": True,
        "stim_dem_modified": True,
        "backend_lowering": "stim_pauli_reduced_source_projection",
        "reason": (
            "A reduced Pauli projection of the source timeline was inserted into "
            "the noisy Stim circuit. Exact source payloads remain evaluator-only "
            "sidecar truth; this is not analog joint-Lindbladian/source truth."
        ),
    }
