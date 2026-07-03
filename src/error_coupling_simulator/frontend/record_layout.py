from __future__ import annotations

"""Structured record layout for frontend-compiled syndrome circuits."""

from dataclasses import dataclass

from .code_spec import CodeSpec


@dataclass(frozen=True)
class RoundMeasurementRecord:
    key: str
    round_index: int
    check_name: str
    ancilla: int

    def to_manifest(self) -> dict:
        return {
            "key": self.key,
            "round_index": self.round_index,
            "check_name": self.check_name,
            "ancilla": self.ancilla,
        }


@dataclass(frozen=True)
class DetectorLayoutRecord:
    name: str
    index: int
    kind: str
    keys: tuple[str, ...]
    coords: tuple[float, ...] = ()

    def to_manifest(self) -> dict:
        return {
            "name": self.name,
            "index": self.index,
            "kind": self.kind,
            "keys": list(self.keys),
            "coords": list(self.coords),
        }


@dataclass(frozen=True)
class FinalDataRecord:
    key: str
    qubit: int
    basis: str

    def to_manifest(self) -> dict:
        return {"key": self.key, "qubit": self.qubit, "basis": self.basis}


@dataclass(frozen=True)
class ObservableLayoutRecord:
    name: str
    index: int
    keys: tuple[str, ...]

    def to_manifest(self) -> dict:
        return {"name": self.name, "index": self.index, "keys": list(self.keys)}


@dataclass(frozen=True)
class RecordLayout:
    """Expected frontend record layout before Stim conversion."""

    schedule_name: str
    round_measurements: tuple[RoundMeasurementRecord, ...]
    detectors: tuple[DetectorLayoutRecord, ...]
    final_data: tuple[FinalDataRecord, ...]
    observables: tuple[ObservableLayoutRecord, ...]

    @property
    def detector_names(self) -> tuple[str, ...]:
        return tuple(record.name for record in self.detectors)

    @property
    def measurement_keys(self) -> tuple[str, ...]:
        return tuple(record.key for record in self.round_measurements) + tuple(
            record.key for record in self.final_data
        )

    @property
    def observable_names(self) -> tuple[str, ...]:
        return tuple(record.name for record in self.observables)

    def to_manifest(self) -> dict:
        return {
            "schedule_name": self.schedule_name,
            "round_measurements": [record.to_manifest() for record in self.round_measurements],
            "detectors": [record.to_manifest() for record in self.detectors],
            "final_data": [record.to_manifest() for record in self.final_data],
            "observables": [record.to_manifest() for record in self.observables],
        }


def build_repeated_memory_record_layout(spec: CodeSpec, *, schedule_name: str) -> RecordLayout:
    round_measurements = tuple(
        RoundMeasurementRecord(
            key=check_key(round_index, check.name),
            round_index=round_index,
            check_name=check.name,
            ancilla=check.ancilla,
        )
        for round_index in range(spec.rounds)
        for check in spec.checks
    )

    detectors: list[DetectorLayoutRecord] = []
    for round_index in range(1, spec.rounds):
        for check in spec.checks:
            detectors.append(
                DetectorLayoutRecord(
                    name=delta_detector_name(check.name, round_index),
                    index=len(detectors),
                    kind="round_delta",
                    keys=(
                        check_key(round_index - 1, check.name),
                        check_key(round_index, check.name),
                    ),
                    coords=tuple(check.coords) + (float(round_index),),
                )
            )
    for check in spec.checks:
        detectors.append(
            DetectorLayoutRecord(
                name=final_detector_name(check.name),
                index=len(detectors),
                kind="final_closure",
                keys=(check_key(spec.rounds - 1, check.name),)
                + tuple(final_key(term.qubit, term.basis) for term in check.terms),
                coords=tuple(check.coords) + (float(spec.rounds),),
            )
        )

    final_data = tuple(
        FinalDataRecord(key=final_key(qubit, basis), qubit=qubit, basis=basis)
        for qubit, basis in sorted(final_measurements(spec).items())
    )
    observables = tuple(
        ObservableLayoutRecord(
            name=logical.name,
            index=logical.index,
            keys=tuple(final_key(term.qubit, term.basis) for term in logical.terms),
        )
        for logical in spec.logical_observables
    )
    return RecordLayout(
        schedule_name=schedule_name,
        round_measurements=round_measurements,
        detectors=tuple(detectors),
        final_data=final_data,
        observables=observables,
    )


def final_measurements(spec: CodeSpec) -> dict[int, str]:
    out: dict[int, str] = {}
    for check in spec.checks:
        for term in check.terms:
            _add_final_measurement(
                out,
                qubit=term.qubit,
                basis=term.basis,
                context=f"final check closure {check.name!r}",
            )
    for logical in spec.logical_observables:
        for term in logical.terms:
            _add_final_measurement(
                out,
                qubit=term.qubit,
                basis=term.basis,
                context=f"final logical observable {logical.name!r}",
            )
    return out


def _add_final_measurement(
    out: dict[int, str],
    *,
    qubit: int,
    basis: str,
    context: str,
) -> None:
    existing = out.get(qubit)
    if existing is not None and existing != basis:
        raise ValueError(
            f"{context} requests incompatible bases for final readout on qubit {qubit}: "
            f"{existing} vs {basis}"
        )
    out[qubit] = basis


def check_key(round_index: int, check_name: str) -> str:
    return f"round{int(round_index)}:{check_name}"


def delta_detector_name(check_name: str, round_index: int) -> str:
    return f"delta:{check_name}:round{int(round_index)}"


def final_detector_name(check_name: str) -> str:
    return f"final:{check_name}"


def final_key(qubit: int, basis: str) -> str:
    return f"final:q{int(qubit)}:{basis}"
