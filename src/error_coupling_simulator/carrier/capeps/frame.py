from __future__ import annotations

"""Exact Clifford-frame adapters for the all-qubit CAPEPS prototype."""

import copy
import importlib
import importlib.metadata
import importlib.util
from dataclasses import dataclass
from typing import Protocol, Sequence, runtime_checkable

import numpy as np
import stim


SDIM_SUPPORTED_VERSION = "1.3.3"
SDIM_INSPECTED_COMMIT = "115c495b23ade35ef0f68b7299afef463129bf51"


class FrameBackendUnavailable(RuntimeError):
    """Raised when an explicitly selected optional frame backend is unavailable."""


@dataclass(frozen=True)
class FrameBackendStatus:
    name: str
    available: bool
    version: str | None
    detail: str


@runtime_checkable
class CliffordFrame(Protocol):
    """The frame in the invariant ``|psi> = C |phi>``."""

    @property
    def num_qubits(self) -> int: ...

    @property
    def backend_name(self) -> str: ...

    def copy(self) -> "CliffordFrame": ...

    def apply_clifford(self, circuit: stim.Circuit) -> None:
        """Apply a physical Clifford as ``C <- U C``."""

    def pullback_pauli(self, pauli: stim.PauliString) -> stim.PauliString:
        """Return the signed Pauli ``C^dagger P C``."""

    def right_compose_inverse(
        self,
        tableau: stim.Tableau,
        targets: Sequence[int],
    ) -> None:
        """Refactor the frame as ``C <- C Q^dagger``."""

    def as_stim_tableau(self) -> stim.Tableau:
        """Return an independent Stim tableau encoding the same frame."""


def _require_num_qubits(num_qubits: int) -> int:
    if isinstance(num_qubits, bool) or not isinstance(num_qubits, int):
        raise TypeError("num_qubits must be an integer")
    if num_qubits <= 0:
        raise ValueError("num_qubits must be positive")
    return num_qubits


def _require_pauli_width(pauli: stim.PauliString, num_qubits: int) -> None:
    if not isinstance(pauli, stim.PauliString):
        raise TypeError("pauli must be a stim.PauliString")
    if len(pauli) != num_qubits:
        raise ValueError(
            f"Pauli width {len(pauli)} does not match frame width {num_qubits}"
        )


def _embedded_tableau(circuit: stim.Circuit, num_qubits: int) -> stim.Tableau:
    if not isinstance(circuit, stim.Circuit):
        raise TypeError("circuit must be a stim.Circuit")
    # Defaults are deliberately strict.  Measurement, reset, and noise are
    # instruments/mechanisms and must never be silently ignored here.
    small = circuit.to_tableau()
    if len(small) > num_qubits:
        raise ValueError(
            f"Clifford circuit width {len(small)} exceeds frame width {num_qubits}"
        )
    if len(small) == num_qubits:
        return small
    out = stim.Tableau(num_qubits)
    if len(small):
        out.append(small, list(range(len(small))))
    return out


def _embedded_local_tableau(
    tableau: stim.Tableau,
    targets: Sequence[int],
    num_qubits: int,
) -> stim.Tableau:
    if not isinstance(tableau, stim.Tableau):
        raise TypeError("tableau must be a stim.Tableau")
    if not isinstance(targets, Sequence) or isinstance(targets, (str, bytes)):
        raise TypeError("targets must be a sequence of qubit indices")
    checked: list[int] = []
    for target in targets:
        if isinstance(target, bool) or not isinstance(target, int):
            raise TypeError("targets must contain integers")
        if target < 0 or target >= num_qubits:
            raise ValueError("target is outside the frame")
        checked.append(target)
    if len(checked) != len(tableau):
        raise ValueError("target count does not match local tableau width")
    if len(set(checked)) != len(checked):
        raise ValueError("targets must be distinct")
    out = stim.Tableau(num_qubits)
    if checked:
        out.append(tableau, checked)
    return out


class StimCliffordFrame:
    """Stim-backed all-qubit frame with explicit left-composition semantics."""

    def __init__(
        self,
        num_qubits: int,
        *,
        tableau: stim.Tableau | None = None,
    ) -> None:
        self._num_qubits = _require_num_qubits(num_qubits)
        if tableau is None:
            self._tableau = stim.Tableau(self._num_qubits)
        else:
            if not isinstance(tableau, stim.Tableau):
                raise TypeError("tableau must be a stim.Tableau")
            if len(tableau) != self._num_qubits:
                raise ValueError("tableau width does not match num_qubits")
            self._tableau = tableau.copy()

    @property
    def num_qubits(self) -> int:
        return self._num_qubits

    @property
    def backend_name(self) -> str:
        return f"stim-{stim.__version__}"

    def copy(self) -> "StimCliffordFrame":
        return StimCliffordFrame(self._num_qubits, tableau=self._tableau)

    def apply_clifford(self, circuit: stim.Circuit) -> None:
        operation = _embedded_tableau(circuit, self._num_qubits)
        # Tableau multiplication follows unitary multiplication:
        # operation * frame is U C, not C U.
        self._tableau = operation * self._tableau

    def pullback_pauli(self, pauli: stim.PauliString) -> stim.PauliString:
        _require_pauli_width(pauli, self._num_qubits)
        # `before` computes C^dagger P C and preserves the exact Pauli sign.
        return pauli.before(
            self._tableau,
            targets=list(range(self._num_qubits)),
        )

    def right_compose_inverse(
        self,
        tableau: stim.Tableau,
        targets: Sequence[int],
    ) -> None:
        operation = _embedded_local_tableau(
            tableau,
            targets,
            self._num_qubits,
        )
        self._tableau = self._tableau * operation.inverse()

    def as_stim_tableau(self) -> stim.Tableau:
        return self._tableau.copy()


def sdim_backend_status() -> FrameBackendStatus:
    """Report whether the source-inspected SDIM API is importable and version-pinned."""

    if importlib.util.find_spec("sdim") is None:
        return FrameBackendStatus(
            name="sdim",
            available=False,
            version=None,
            detail=(
                "sdim is not importable; the optional qubit bridge targets "
                f"{SDIM_SUPPORTED_VERSION}"
            ),
        )
    try:
        version = importlib.metadata.version("sdim")
    except importlib.metadata.PackageNotFoundError:
        return FrameBackendStatus(
            name="sdim",
            available=False,
            version=None,
            detail="sdim is importable but has no installed distribution identity",
        )
    if version != SDIM_SUPPORTED_VERSION:
        return FrameBackendStatus(
            name="sdim",
            available=False,
            version=version,
            detail=(
                f"unsupported sdim version {version}; expected "
                f"{SDIM_SUPPORTED_VERSION}"
            ),
        )
    try:
        module = importlib.import_module("sdim")
    except Exception as exc:
        return FrameBackendStatus(
            name="sdim",
            available=False,
            version=version,
            detail=(
                "sdim distribution is present but its runtime import failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        )
    if getattr(module, "ExtendedTableau", None) is None:
        return FrameBackendStatus(
            name="sdim",
            available=False,
            version=version,
            detail="sdim.ExtendedTableau is unavailable",
        )
    return FrameBackendStatus(
        name="sdim",
        available=True,
        version=version,
        detail=(
            "qubit-only bridge; generalized qudit/leakage semantics remain unsupported"
        ),
    )


def _sdim_generator_to_stim_pauli(
    x_column: np.ndarray,
    z_column: np.ndarray,
    phase: int,
) -> stim.PauliString:
    """Translate one SDIM qubit generator ``i^p X^x Z^z`` without losing sign."""

    x = np.asarray(x_column)
    z = np.asarray(z_column)
    if x.ndim != 1 or z.ndim != 1 or x.shape != z.shape:
        raise ValueError("SDIM generator X/Z columns must be equal-length vectors")
    if not np.issubdtype(x.dtype, np.integer) or not np.issubdtype(
        z.dtype, np.integer
    ):
        raise TypeError("SDIM generator columns must have integer dtype")
    x = x % 2
    z = z % 2
    labels: list[str] = []
    y_count = 0
    for xb, zb in zip(x.tolist(), z.tolist(), strict=True):
        if xb == 0 and zb == 0:
            labels.append("_")
        elif xb == 1 and zb == 0:
            labels.append("X")
        elif xb == 0 and zb == 1:
            labels.append("Z")
        else:
            labels.append("Y")
            y_count += 1

    # SDIM stores i^phase X^x Z^z.  Stim's Y label already includes i XZ.
    relative = (int(phase) - y_count) % 4
    if relative == 0:
        prefix = "+"
    elif relative == 2:
        prefix = "-"
    else:
        raise ValueError("SDIM generator is not Hermitian after phase translation")
    return stim.PauliString(prefix + "".join(labels))


class SdimCliffordFrame:
    """Optional SDIM 1.3.3 qubit frame with a signed Stim pullback bridge.

    SDIM owns the generator updates.  Stim is used only to translate those
    generators into the common signed-Pauli pullback interface.  Dimension
    greater than two is rejected because this package's residual backends are
    qubit PEPS, not generalized-qudit or leakage-qutrit states.
    """

    def __init__(self, num_qubits: int) -> None:
        self._num_qubits = _require_num_qubits(num_qubits)
        status = sdim_backend_status()
        if not status.available:
            raise FrameBackendUnavailable(status.detail)
        module = importlib.import_module("sdim")
        tableau_type = getattr(module, "ExtendedTableau", None)
        if tableau_type is None:
            raise FrameBackendUnavailable("sdim.ExtendedTableau is unavailable")
        self._sdim_version = status.version
        self._tableau = tableau_type(
            num_qudits=self._num_qubits,
            dimension=2,
        )
        # SDIM owns left physical updates A <- U A.  A separate Stim
        # post-frame B makes exact residual refactors C=A B <- A B Q^dagger
        # possible without misusing SDIM's left-update API as a right update.
        self._post_tableau = stim.Tableau(self._num_qubits)

    @property
    def num_qubits(self) -> int:
        return self._num_qubits

    @property
    def backend_name(self) -> str:
        return f"sdim-{self._sdim_version}-qubit-bridge"

    def copy(self) -> "SdimCliffordFrame":
        out = object.__new__(SdimCliffordFrame)
        out._num_qubits = self._num_qubits
        out._sdim_version = self._sdim_version
        out._tableau = copy.deepcopy(self._tableau)
        out._post_tableau = self._post_tableau.copy()
        return out

    @staticmethod
    def _single(tableau, name: str, target: int) -> None:
        if name == "I":
            return
        if name == "H":
            tableau.hadamard(target)
            return
        if name == "S":
            tableau.phase(target)
            return
        if name == "S_DAG":
            tableau.phase_inv(target)
            return
        if name == "X":
            tableau.hadamard(target)
            tableau.phase(target)
            tableau.phase(target)
            tableau.hadamard(target)
            return
        if name == "Z":
            tableau.phase(target)
            tableau.phase(target)
            return
        if name == "Y":
            # XZ differs from Y by a global phase, irrelevant to conjugation.
            SdimCliffordFrame._single(tableau, "X", target)
            SdimCliffordFrame._single(tableau, "Z", target)
            return
        raise ValueError(f"unsupported SDIM single-qubit Clifford {name!r}")

    @staticmethod
    def _pair(tableau, name: str, left: int, right: int) -> None:
        if left == right:
            raise ValueError(f"{name} targets must be distinct")
        if name in ("CX", "CNOT"):
            tableau.cnot(left, right)
            return
        if name == "CZ":
            tableau.hadamard(right)
            tableau.cnot(left, right)
            tableau.hadamard(right)
            return
        if name == "SWAP":
            tableau.cnot(left, right)
            tableau.cnot(right, left)
            tableau.cnot(left, right)
            return
        raise ValueError(f"unsupported SDIM two-qubit Clifford {name!r}")

    def apply_clifford(self, circuit: stim.Circuit) -> None:
        # First reject any non-unitary/non-Clifford Stim instruction without
        # allowing an SDIM-side partial mutation.
        _embedded_tableau(circuit, self._num_qubits)
        candidate = copy.deepcopy(self._tableau)
        for instruction in circuit.flattened():
            if not isinstance(instruction, stim.CircuitInstruction):
                raise TypeError("flattened Stim circuit contained a non-instruction")
            name = instruction.name
            if name in ("TICK", "QUBIT_COORDS", "SHIFT_COORDS"):
                continue
            targets = instruction.targets_copy()
            if any(not target.is_qubit_target for target in targets):
                raise ValueError(
                    f"SDIM bridge does not accept non-qubit targets in {name}"
                )
            qubits = [int(target.qubit_value) for target in targets]
            if any(q < 0 or q >= self._num_qubits for q in qubits):
                raise ValueError("SDIM Clifford target is outside the frame")
            if name in ("I", "H", "S", "S_DAG", "X", "Y", "Z"):
                for qubit in qubits:
                    self._single(candidate, name, qubit)
            elif name in ("CX", "CNOT", "CZ", "SWAP"):
                if len(qubits) % 2:
                    raise ValueError(f"{name} requires target pairs")
                for offset in range(0, len(qubits), 2):
                    self._pair(candidate, name, qubits[offset], qubits[offset + 1])
            else:
                raise ValueError(
                    f"Stim Clifford {name!r} has no frozen SDIM bridge mapping"
                )
        candidate.modulo()
        # Validate the full generator set before committing.
        self._stim_tableau_from_sdim(candidate, self._num_qubits)
        self._tableau = candidate

    @staticmethod
    def _stim_tableau_from_sdim(tab, num_qubits: int) -> stim.Tableau:
        xs = [
            _sdim_generator_to_stim_pauli(
                tab.destab_x_block[:, index],
                tab.destab_z_block[:, index],
                int(tab.destab_phase_vector[index]),
            )
            for index in range(num_qubits)
        ]
        zs = [
            _sdim_generator_to_stim_pauli(
                tab.x_block[:, index],
                tab.z_block[:, index],
                int(tab.phase_vector[index]),
            )
            for index in range(num_qubits)
        ]
        return stim.Tableau.from_conjugated_generators(xs=xs, zs=zs)

    def as_stim_tableau(self) -> stim.Tableau:
        left = self._stim_tableau_from_sdim(
            self._tableau,
            self._num_qubits,
        )
        return left * self._post_tableau

    def right_compose_inverse(
        self,
        tableau: stim.Tableau,
        targets: Sequence[int],
    ) -> None:
        operation = _embedded_local_tableau(
            tableau,
            targets,
            self._num_qubits,
        )
        self._post_tableau = self._post_tableau * operation.inverse()

    def pullback_pauli(self, pauli: stim.PauliString) -> stim.PauliString:
        _require_pauli_width(pauli, self._num_qubits)
        tableau = self.as_stim_tableau()
        return pauli.before(
            tableau,
            targets=list(range(self._num_qubits)),
        )
