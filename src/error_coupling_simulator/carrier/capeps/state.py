from __future__ import annotations

"""Hybrid state and branch ledger for ``|psi> = C |phi>``."""

import math
import numbers
from dataclasses import dataclass
from typing import Sequence

import numpy as np
import stim

from ...numerics import NUMERICAL_ZERO
from .algebra import (
    TableauGeneratorBasis,
    TableauPauliDecomposition,
    apply_local_tableau_to_vector,
    expand_local_unitary_to_paulis,
    require_targets,
)
from .frame import CliffordFrame, StimCliffordFrame
from .residual import (
    CDTYPE,
    DenseResidual,
    PauliTerm,
    QuimbPepsResidual,
    ResidualState,
    ResidualStateError,
    ResidualUpdate,
    ZeroProbabilityBranch,
)


@dataclass(frozen=True)
class CoherentUpdate:
    physical_terms: tuple[tuple[complex, str], ...]
    pulled_back_terms: tuple[tuple[complex, str], ...]
    tableau_decompositions: tuple[TableauPauliDecomposition, ...]
    norm_squared_before: float
    norm_squared_after: float
    residual_update: ResidualUpdate


@dataclass(frozen=True)
class CliffordRefactor:
    targets: tuple[int, ...]
    tableau: str
    norm_squared_before: float
    norm_squared_after: float
    frame_backend: str
    residual_backend: str
    residual_update: ResidualUpdate


@dataclass(frozen=True)
class PauliExpectation:
    physical_pauli: str
    pulled_back_pauli: str
    value: float
    frame_backend: str
    residual_backend: str


@dataclass(frozen=True)
class MeasurementEvent:
    column: int
    physical_pauli: str
    pulled_back_pauli: str
    outcome: int
    conditional_probability: float
    cumulative_log_mass: float
    reset_to_zero: bool
    frame_backend: str
    residual_backend: str
    residual_update: ResidualUpdate


@dataclass(frozen=True)
class MeasurementBranch:
    outcome: int
    conditional_probability: float
    state: "CAPEPSState | None"


def _require_real_finite(value: float, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise TypeError(f"{name} must be a real scalar")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return float(value)


def _copy_physical_terms(
    terms: Sequence[PauliTerm],
    num_qubits: int,
) -> tuple[PauliTerm, ...]:
    if not isinstance(terms, Sequence) or isinstance(terms, (str, bytes)):
        raise TypeError("terms must be a sequence")
    if not terms:
        raise ValueError("a coherent Pauli expansion needs at least one term")
    out: list[PauliTerm] = []
    for item in terms:
        if not isinstance(item, tuple) or len(item) != 2:
            raise TypeError("each term must be a (coefficient, PauliString) tuple")
        coefficient, pauli = item
        if isinstance(coefficient, bool) or not isinstance(
            coefficient, numbers.Complex
        ):
            raise TypeError("Pauli coefficient must be a real or complex scalar")
        if not np.isfinite(coefficient):
            raise ValueError("Pauli coefficient must be finite")
        if not isinstance(pauli, stim.PauliString):
            raise TypeError("Pauli terms must use stim.PauliString")
        if len(pauli) != num_qubits:
            raise ValueError(
                f"Pauli width {len(pauli)} does not match state width {num_qubits}"
            )
        out.append((complex(coefficient), stim.PauliString(str(pauli))))
    return tuple(out)


def _require_hermitian_pauli(
    pauli: stim.PauliString,
    num_qubits: int,
) -> stim.PauliString:
    if not isinstance(pauli, stim.PauliString):
        raise TypeError("pauli must be a stim.PauliString")
    if len(pauli) != num_qubits:
        raise ValueError(
            f"Pauli width {len(pauli)} does not match state width {num_qubits}"
        )
    copied = stim.PauliString(str(pauli))
    if complex(copied.sign) not in (1.0 + 0.0j, -1.0 + 0.0j):
        raise ValueError("measurement and rotation require a Hermitian signed Pauli")
    return copied


def _reset_qubit(pauli: stim.PauliString) -> int:
    if complex(pauli.sign) != 1.0:
        raise ValueError("measure-reset requires physical +Z, not a signed variant")
    support = [index for index in range(len(pauli)) if int(pauli[index]) != 0]
    if len(support) != 1 or int(pauli[support[0]]) != 3:
        raise ValueError("reset_to_zero is supported only for physical +Z_q")
    return support[0]


class CAPEPSState:
    """A Clifford frame plus a coherent residual state.

    The measurement ledger contains raw conditional branches only.  It is not
    a temporal detector/observable ``RecordBatch``.
    """

    def __init__(
        self,
        frame: CliffordFrame,
        residual: ResidualState,
        *,
        branch_log_mass: float = 0.0,
        measurement_events: Sequence[MeasurementEvent] = (),
    ) -> None:
        if not isinstance(frame, CliffordFrame):
            raise TypeError("frame does not satisfy the CliffordFrame protocol")
        if not isinstance(residual, ResidualState):
            raise TypeError("residual does not satisfy the ResidualState protocol")
        if frame.num_qubits != residual.num_qubits:
            raise ValueError("frame and residual widths differ")
        log_mass = _require_real_finite(branch_log_mass, name="branch_log_mass")
        events = tuple(measurement_events)
        if any(not isinstance(event, MeasurementEvent) for event in events):
            raise TypeError("measurement_events contains a non-MeasurementEvent")
        if tuple(event.column for event in events) != tuple(range(len(events))):
            raise ValueError("measurement event columns must be contiguous from zero")
        frame_snapshot = frame.copy()
        residual_snapshot = residual.copy()
        if not isinstance(frame_snapshot, CliffordFrame):
            raise TypeError("frame.copy() did not return a CliffordFrame")
        if not isinstance(residual_snapshot, ResidualState):
            raise TypeError("residual.copy() did not return a ResidualState")
        norm = residual_snapshot.norm_squared()
        if not math.isfinite(norm) or norm <= 0.0:
            raise ResidualStateError("CAPEPS residual must have positive finite norm")
        self._frame = frame_snapshot
        self._residual = residual_snapshot
        self._branch_log_mass = log_mass
        self._measurement_events = list(events)

    @classmethod
    def dense_zero(
        cls,
        num_qubits: int,
        *,
        frame: CliffordFrame | None = None,
    ) -> "CAPEPSState":
        active_frame = (
            StimCliffordFrame(num_qubits) if frame is None else frame
        )
        return cls(active_frame, DenseResidual.zero(num_qubits))

    @classmethod
    def peps_zero(
        cls,
        shape: tuple[int, int],
        *,
        frame: CliffordFrame | None = None,
        contraction_optimize: str = "auto-hq",
    ) -> "CAPEPSState":
        num_qubits = shape[0] * shape[1]
        active_frame = (
            StimCliffordFrame(num_qubits) if frame is None else frame
        )
        residual = QuimbPepsResidual.product_state(
            shape,
            contraction_optimize=contraction_optimize,
        )
        return cls(active_frame, residual)

    @property
    def num_qubits(self) -> int:
        return self._frame.num_qubits

    @property
    def frame(self) -> CliffordFrame:
        return self._frame.copy()

    @property
    def residual(self) -> ResidualState:
        return self._residual.copy()

    @property
    def branch_log_mass(self) -> float:
        return self._branch_log_mass

    @property
    def measurement_events(self) -> tuple[MeasurementEvent, ...]:
        return tuple(self._measurement_events)

    @property
    def raw_outcomes(self) -> tuple[int, ...]:
        return tuple(event.outcome for event in self._measurement_events)

    def copy(self) -> "CAPEPSState":
        return CAPEPSState(
            self._frame,
            self._residual,
            branch_log_mass=self._branch_log_mass,
            measurement_events=self._measurement_events,
        )

    def apply_clifford(self, circuit: stim.Circuit) -> None:
        candidate = self._frame.copy()
        candidate.apply_clifford(circuit)
        self._frame = candidate

    def apply_pauli_expansion(
        self,
        terms: Sequence[PauliTerm],
        *,
        require_norm_preserving: bool = True,
        norm_tolerance: float = NUMERICAL_ZERO,
    ) -> CoherentUpdate:
        physical = _copy_physical_terms(terms, self.num_qubits)
        if not isinstance(require_norm_preserving, bool):
            raise TypeError("require_norm_preserving must be bool")
        tolerance = _require_real_finite(norm_tolerance, name="norm_tolerance")
        if tolerance < 0.0:
            raise ValueError("norm_tolerance must be nonnegative")
        tableau = self._frame.as_stim_tableau()
        generator_basis = TableauGeneratorBasis(tableau)
        decompositions = tuple(
            generator_basis.decompose(pauli)
            for _, pauli in physical
        )
        pulled = tuple(
            (coefficient, self._frame.pullback_pauli(pauli))
            for coefficient, pauli in physical
        )
        if tuple(str(pauli) for _, pauli in pulled) != tuple(
            item.pulled_back_pauli for item in decompositions
        ):
            raise ResidualStateError(
                "Eq. (5) ledger disagrees with frame signed pullback"
            )
        candidate = self._residual.copy()
        before = candidate.norm_squared()
        residual_update = candidate.apply_pauli_sum(pulled)
        after = candidate.norm_squared()
        if require_norm_preserving:
            discrepancy = abs(after - before)
            if discrepancy > tolerance * max(1.0, before):
                raise ResidualStateError(
                    "coherent update failed the declared norm-preservation gate: "
                    f"|{after} - {before}| = {discrepancy} > {tolerance}"
                )
        self._residual = candidate
        return CoherentUpdate(
            physical_terms=tuple(
                (coefficient, str(pauli)) for coefficient, pauli in physical
            ),
            pulled_back_terms=tuple(
                (coefficient, str(pauli)) for coefficient, pauli in pulled
            ),
            tableau_decompositions=decompositions,
            norm_squared_before=before,
            norm_squared_after=after,
            residual_update=residual_update,
        )

    def apply_local_unitary(
        self,
        unitary: np.ndarray,
        targets: Sequence[int],
        *,
        norm_tolerance: float = NUMERICAL_ZERO,
        max_local_qubits: int = 2,
    ) -> CoherentUpdate:
        terms = expand_local_unitary_to_paulis(
            unitary,
            targets,
            num_qubits=self.num_qubits,
            max_local_qubits=max_local_qubits,
        )
        return self.apply_pauli_expansion(
            terms,
            require_norm_preserving=True,
            norm_tolerance=norm_tolerance,
        )

    def apply_pauli_rotation(
        self,
        pauli: stim.PauliString,
        angle_radians: float,
        *,
        norm_tolerance: float = NUMERICAL_ZERO,
    ) -> CoherentUpdate:
        physical = _require_hermitian_pauli(pauli, self.num_qubits)
        angle = _require_real_finite(angle_radians, name="angle_radians")
        half = 0.5 * angle
        identity = stim.PauliString(self.num_qubits)
        return self.apply_pauli_expansion(
            (
                (complex(math.cos(half)), identity),
                (-1.0j * math.sin(half), physical),
            ),
            require_norm_preserving=True,
            norm_tolerance=norm_tolerance,
        )

    def apply_ry(
        self,
        qubit: int,
        angle_radians: float,
        *,
        norm_tolerance: float = NUMERICAL_ZERO,
    ) -> CoherentUpdate:
        if isinstance(qubit, bool) or not isinstance(qubit, int):
            raise TypeError("qubit must be an integer")
        if qubit < 0 or qubit >= self.num_qubits:
            raise ValueError("qubit is outside the state")
        pauli = stim.PauliString(self.num_qubits)
        pauli[qubit] = 2
        return self.apply_pauli_rotation(
            pauli,
            angle_radians,
            norm_tolerance=norm_tolerance,
        )

    def refactor_residual_clifford(
        self,
        tableau: stim.Tableau,
        targets: Sequence[int],
        *,
        norm_tolerance: float = NUMERICAL_ZERO,
    ) -> CliffordRefactor:
        if not isinstance(tableau, stim.Tableau):
            raise TypeError("tableau must be a stim.Tableau")
        checked = require_targets(
            targets,
            num_qubits=self.num_qubits,
            expected_count=len(tableau),
        )
        tolerance = _require_real_finite(norm_tolerance, name="norm_tolerance")
        if tolerance < 0.0:
            raise ValueError("norm_tolerance must be nonnegative")
        frame_candidate = self._frame.copy()
        residual_candidate = self._residual.copy()
        before = residual_candidate.norm_squared()
        residual_update = residual_candidate.apply_local_clifford(
            tableau,
            checked,
        )
        frame_candidate.right_compose_inverse(tableau, checked)
        after = residual_candidate.norm_squared()
        discrepancy = abs(after - before)
        if discrepancy > tolerance * max(1.0, before):
            raise ResidualStateError(
                "Clifford refactor failed norm preservation: "
                f"|{after} - {before}| = {discrepancy} > {tolerance}"
            )
        self._frame = frame_candidate
        self._residual = residual_candidate
        return CliffordRefactor(
            targets=checked,
            tableau=str(tableau),
            norm_squared_before=before,
            norm_squared_after=after,
            frame_backend=frame_candidate.backend_name,
            residual_backend=residual_candidate.backend_name,
            residual_update=residual_update,
        )

    def expectation_pauli(
        self,
        pauli: stim.PauliString,
    ) -> PauliExpectation:
        physical = _require_hermitian_pauli(pauli, self.num_qubits)
        pulled = self._frame.pullback_pauli(physical)
        raw = self._residual.expectation_pauli(pulled)
        if not math.isfinite(raw.real) or not math.isfinite(raw.imag):
            raise ResidualStateError("Pauli expectation is non-finite")
        scale = max(1.0, abs(raw.real))
        if abs(raw.imag) > NUMERICAL_ZERO * scale:
            raise ResidualStateError(
                f"Hermitian Pauli expectation has imaginary residual {raw.imag}"
            )
        value = float(raw.real)
        if abs(value) > 1.0 + NUMERICAL_ZERO:
            raise ResidualStateError(
                f"Pauli expectation lies outside [-1, 1]: {value}"
            )
        value = min(1.0, max(-1.0, value))
        return PauliExpectation(
            physical_pauli=str(physical),
            pulled_back_pauli=str(pulled),
            value=value,
            frame_backend=self._frame.backend_name,
            residual_backend=self._residual.backend_name,
        )

    def measure_pauli(
        self,
        pauli: stim.PauliString,
        outcome: int,
        *,
        reset_to_zero: bool = False,
    ) -> MeasurementEvent:
        physical = _require_hermitian_pauli(pauli, self.num_qubits)
        if not isinstance(reset_to_zero, bool):
            raise TypeError("reset_to_zero must be bool")
        reset_qubit = _reset_qubit(physical) if reset_to_zero else None
        pulled = self._frame.pullback_pauli(physical)
        residual_candidate = self._residual.copy()
        frame_candidate = self._frame.copy()
        probability, residual_update = residual_candidate.project_pauli(
            pulled,
            outcome,
        )
        if reset_qubit is not None and outcome == 1:
            reset_circuit = stim.Circuit()
            reset_circuit.append("X", [reset_qubit])
            frame_candidate.apply_clifford(reset_circuit)
        cumulative = math.fsum(
            (self._branch_log_mass, math.log(probability))
        )
        event = MeasurementEvent(
            column=len(self._measurement_events),
            physical_pauli=str(physical),
            pulled_back_pauli=str(pulled),
            outcome=outcome,
            conditional_probability=probability,
            cumulative_log_mass=cumulative,
            reset_to_zero=reset_to_zero,
            frame_backend=frame_candidate.backend_name,
            residual_backend=residual_candidate.backend_name,
            residual_update=residual_update,
        )
        self._residual = residual_candidate
        self._frame = frame_candidate
        self._branch_log_mass = cumulative
        self._measurement_events.append(event)
        return event

    def fork_measurement(
        self,
        pauli: stim.PauliString,
        *,
        reset_to_zero: bool = False,
    ) -> tuple[MeasurementBranch, MeasurementBranch]:
        physical = _require_hermitian_pauli(pauli, self.num_qubits)
        branches: list[MeasurementBranch] = []
        for outcome in (0, 1):
            child = self.copy()
            try:
                event = child.measure_pauli(
                    physical,
                    outcome,
                    reset_to_zero=reset_to_zero,
                )
            except ZeroProbabilityBranch:
                branches.append(
                    MeasurementBranch(
                        outcome=outcome,
                        conditional_probability=0.0,
                        state=None,
                    )
                )
            else:
                branches.append(
                    MeasurementBranch(
                        outcome=outcome,
                        conditional_probability=event.conditional_probability,
                        state=child,
                    )
                )
        return branches[0], branches[1]

    def physical_state_vector(self, *, max_qubits: int = 12) -> np.ndarray:
        residual = self._residual.state_vector(max_qubits=max_qubits)
        tableau = self._frame.as_stim_tableau()
        vector = apply_local_tableau_to_vector(
            residual,
            tableau,
            tuple(range(self.num_qubits)),
            num_qubits=self.num_qubits,
        )
        if vector.dtype != CDTYPE or not np.isfinite(vector).all():
            raise ResidualStateError(
                "physical state materialization did not produce finite complex128"
            )
        out = np.array(vector, copy=True)
        out.setflags(write=False)
        return out
