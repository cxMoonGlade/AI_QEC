from __future__ import annotations

"""Ideal frontend gate controls lowered as Axis-1 Hamiltonian terms.

The generic Axis-1 record/state path uses these controls to keep frontend gate
semantics inside the same substep generator as the local noise primitives. This
is separate from the joint-channel comparison path, where `DR` remains the registered
drive-vs-ZZ witness primitive.
"""

from dataclasses import dataclass
import math
from typing import Any

from .axis1_selection import (
    AXIS1_FRONTEND_TWO_QUBIT_CONTROL_GATES,
    Axis1MechanismSelection,
)


@dataclass(frozen=True)
class Axis1IdealControlRecord:
    """JSON-safe description of one ideal frontend control Hamiltonian."""

    name: str
    gate_name: str
    generator_kind: str
    coefficient: float
    support: tuple[int, ...]
    source_step_indices: tuple[int, ...]
    epistemic_class: str = "a"

    def to_manifest(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "gate_name": self.gate_name,
            "generator_kind": self.generator_kind,
            "coefficient": self.coefficient,
            "support": list(self.support),
            "source_step_indices": list(self.source_step_indices),
            "epistemic_class": self.epistemic_class,
        }


@dataclass(frozen=True)
class Axis1IdealControlBundle:
    """Hamiltonian controls for one schedule-derived selection."""

    H_list: tuple[Any, ...]
    records: tuple[Axis1IdealControlRecord, ...]


def lower_ideal_controls_for_selection(
    selection: Axis1MechanismSelection,
    *,
    dt_ns: float,
    device: str = "cuda",
) -> Axis1IdealControlBundle:
    """Lower ideal frontend gate operations to local Hamiltonian terms."""

    dt = float(dt_ns)
    if dt <= 0.0:
        raise ValueError("dt_ns must be positive for ideal control lowering")
    if selection.substep_kind == "one_qubit_gate":
        return _one_qubit_control(selection, dt_ns=dt, device=device)
    if selection.substep_kind == "two_qubit_gate":
        return _two_qubit_control(selection, dt_ns=dt, device=device)
    return Axis1IdealControlBundle(H_list=(), records=())


def _one_qubit_control(
    selection: Axis1MechanismSelection,
    *,
    dt_ns: float,
    device: str,
) -> Axis1IdealControlBundle:
    active_targets = _active_one_qubit_targets(selection)
    participant_index = {int(q): index for index, q in enumerate(selection.participant)}
    H_list: list[Any] = []
    records: list[Axis1IdealControlRecord] = []
    for active in active_targets:
        op = _operation_record_for_target(selection, active)
        gate = str(op["name"]).upper()
        local, coeff = _one_qubit_generator_and_coefficient(gate, dt_ns, device=device)
        local_index = participant_index[int(active)]
        H_list.append(
            _embed_one_qubit_operator(
                coeff * local,
                target_index=local_index,
                num_qubits=len(selection.participant),
                device=device,
            )
        )
        records.append(
            Axis1IdealControlRecord(
                name=f"CTRL_{gate}",
                gate_name=gate,
                generator_kind="su2_axis_hamiltonian",
                coefficient=coeff,
                support=(local_index,),
                source_step_indices=(int(op["source_step_index"]),),
            )
        )
    return Axis1IdealControlBundle(H_list=tuple(H_list), records=tuple(records))


def _active_one_qubit_targets(selection: Axis1MechanismSelection) -> tuple[int, ...]:
    targets: set[int] = set()
    for op in selection.operation_records:
        for target in op.get("targets", ()):
            q = int(target)
            if q in set(selection.participant):
                targets.add(q)
    ordered = tuple(int(q) for q in selection.participant if int(q) in targets)
    if not ordered:
        raise ValueError(f"selection {selection.selection_id!r} has no active one-qubit targets")
    return ordered


def _two_qubit_control(
    selection: Axis1MechanismSelection,
    *,
    dt_ns: float,
    device: str,
) -> Axis1IdealControlBundle:
    participant_index = {int(q): index for index, q in enumerate(selection.participant)}
    H_list: list[Any] = []
    records: list[Axis1IdealControlRecord] = []
    for op in selection.operation_records:
        gate = str(op["name"]).upper()
        if gate not in AXIS1_FRONTEND_TWO_QUBIT_CONTROL_GATES:
            continue
        generator, coeff = _two_qubit_generator_and_coefficient(gate, dt_ns, device=device)
        for pair in _operation_record_pairs(op):
            if pair[0] not in participant_index or pair[1] not in participant_index:
                continue
            left_index = participant_index[pair[0]]
            right_index = participant_index[pair[1]]
            H_list.append(
                coeff
                * _embed_two_qubit_operator(
                    generator,
                    left_index=left_index,
                    right_index=right_index,
                    num_qubits=len(selection.participant),
                    device=device,
                )
            )
            records.append(
                Axis1IdealControlRecord(
                    name=f"CTRL_{gate}",
                    gate_name=gate,
                    generator_kind="hamiltonian",
                    coefficient=coeff,
                    support=(left_index, right_index),
                    source_step_indices=(int(op["source_step_index"]),),
                )
            )
    if not H_list:
        raise ValueError(
            f"selection {selection.selection_id!r} has no supported two-qubit control"
        )
    return Axis1IdealControlBundle(H_list=tuple(H_list), records=tuple(records))


def _one_qubit_generator_and_coefficient(gate: str, dt_ns: float, *, device: str):
    import torch

    U = _one_qubit_control_matrix(gate, device=device)
    generator, angle = _su2_axis_angle_generator(U, device=device)
    return generator, angle / float(dt_ns)


def _one_qubit_control_matrix(gate: str, *, device: str):
    import torch

    cdt = torch.complex128
    inv_sqrt2 = 1.0 / math.sqrt(2.0)
    if gate == "H":
        return inv_sqrt2 * torch.tensor([[1.0, 1.0], [1.0, -1.0]], dtype=cdt, device=device)
    if gate == "H_XY":
        return torch.tensor([[0.0, 1.0], [1.0j, 0.0]], dtype=cdt, device=device)
    if gate == "H_XZ":
        return inv_sqrt2 * torch.tensor([[1.0, 1.0], [1.0, -1.0]], dtype=cdt, device=device)
    if gate == "C_XYZ":
        return inv_sqrt2 * torch.tensor(
            [[1.0, -1.0j], [1.0, 1.0j]],
            dtype=cdt,
            device=device,
        )
    if gate == "C_ZYX":
        return inv_sqrt2 * torch.tensor(
            [[1.0, 1.0], [1.0j, -1.0j]],
            dtype=cdt,
            device=device,
        )
    if gate == "X":
        return torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=device)
    if gate == "Y":
        return torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=device)
    if gate == "Z":
        return torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=device)
    if gate == "S":
        return torch.tensor([[1.0, 0.0], [0.0, 1.0j]], dtype=cdt, device=device)
    if gate == "S_DAG":
        return torch.tensor([[1.0, 0.0], [0.0, -1.0j]], dtype=cdt, device=device)
    if gate == "SQRT_Z":
        return torch.tensor([[1.0, 0.0], [0.0, 1.0j]], dtype=cdt, device=device)
    if gate == "SQRT_Z_DAG":
        return torch.tensor([[1.0, 0.0], [0.0, -1.0j]], dtype=cdt, device=device)
    if gate == "SQRT_X":
        return inv_sqrt2 * torch.tensor(
            [[1.0, -1.0j], [-1.0j, 1.0]],
            dtype=cdt,
            device=device,
        )
    if gate == "SQRT_X_DAG":
        return inv_sqrt2 * torch.tensor(
            [[1.0, 1.0j], [1.0j, 1.0]],
            dtype=cdt,
            device=device,
        )
    if gate == "SQRT_Y":
        return inv_sqrt2 * torch.tensor(
            [[1.0, -1.0], [1.0, 1.0]],
            dtype=cdt,
            device=device,
        )
    if gate == "SQRT_Y_DAG":
        return inv_sqrt2 * torch.tensor(
            [[1.0, 1.0], [-1.0, 1.0]],
            dtype=cdt,
            device=device,
        )
    raise ValueError(f"unsupported ideal one-qubit Axis-1 control gate {gate!r}")


def _su2_axis_angle_generator(U, *, device: str):
    import torch

    U = torch.as_tensor(U, dtype=torch.complex128, device=device)
    det = torch.linalg.det(U)
    phase = 0.5 * float(torch.angle(det).item())
    global_phase = torch.tensor(
        complex(math.cos(-phase), math.sin(-phase)),
        dtype=torch.complex128,
        device=device,
    )
    V = global_phase * U
    eye = torch.eye(2, dtype=torch.complex128, device=device)
    cos_theta = float((torch.trace(V).real / 2.0).item())
    cos_theta = max(-1.0, min(1.0, cos_theta))
    theta = math.acos(cos_theta)
    sin_theta = math.sin(theta)
    if abs(sin_theta) <= 1.0e-12:
        raise ValueError("degenerate one-qubit control has no nontrivial SU(2) axis")
    generator = (V - cos_theta * eye) / (-1j * sin_theta)
    generator = 0.5 * (generator + generator.conj().transpose(-1, -2))
    return generator, theta


def _two_qubit_generator_and_coefficient(gate: str, dt_ns: float, *, device: str):
    import torch

    cdt = torch.complex128
    if gate == "CZ":
        n = torch.tensor([[0.0, 0.0], [0.0, 1.0]], dtype=cdt, device=device)
        return torch.kron(n.contiguous(), n.contiguous()), math.pi / dt_ns
    if gate == "CX":
        cx = torch.tensor(
            [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]],
            dtype=cdt,
            device=device,
        )
        return cx, math.pi / (2.0 * dt_ns)
    if gate in AXIS1_FRONTEND_TWO_QUBIT_CONTROL_GATES:
        return _principal_hamiltonian_from_unitary(
            _stim_two_qubit_control_matrix(gate, device=device),
            device=device,
        ), 1.0 / dt_ns
    raise ValueError(f"unsupported ideal two-qubit Axis-1 control gate {gate!r}")


def _stim_two_qubit_control_matrix(gate: str, *, device: str):
    import stim
    import torch

    circuit = stim.Circuit(f"{gate} 0 1")
    return torch.as_tensor(
        circuit.to_tableau().to_unitary_matrix(endian="big"),
        dtype=torch.complex128,
        device=device,
    )


def _principal_hamiltonian_from_unitary(U, *, device: str):
    import torch

    U = torch.as_tensor(U, dtype=torch.complex128, device=device)
    dim = int(U.shape[0])
    det = torch.linalg.det(U)
    phase = float(torch.angle(det).item()) / float(dim)
    global_phase = torch.tensor(
        complex(math.cos(-phase), math.sin(-phase)),
        dtype=torch.complex128,
        device=device,
    )
    V = global_phase * U
    eigvals, eigvecs = torch.linalg.eig(V)
    angles = -torch.angle(eigvals).to(torch.float64)
    hamiltonian = (
        eigvecs
        @ torch.diag(angles.to(torch.complex128))
        @ torch.linalg.inv(eigvecs)
    )
    return 0.5 * (hamiltonian + hamiltonian.conj().transpose(-1, -2))


def _operation_record_for_target(
    selection: Axis1MechanismSelection,
    target: int,
) -> dict[str, Any]:
    for op in selection.operation_records:
        targets = tuple(int(q) for q in op.get("targets", ()))
        if int(target) in targets:
            return dict(op)
    raise ValueError(
        f"selection {selection.selection_id!r} has no operation record for target {target}"
    )


def _operation_record_for_pair(
    selection: Axis1MechanismSelection,
    pair: tuple[int, int],
) -> dict[str, Any]:
    wanted = tuple(int(q) for q in pair)
    normal_wanted = tuple(sorted(wanted))
    for op in selection.operation_records:
        targets = tuple(int(q) for q in op.get("targets", ()))
        for i in range(0, len(targets), 2):
            candidate = targets[i : i + 2]
            if tuple(sorted(candidate)) == normal_wanted:
                return dict(op)
    raise ValueError(
        f"selection {selection.selection_id!r} has no operation record for pair {wanted}"
    )


def _operation_record_pairs(op: dict[str, Any]) -> tuple[tuple[int, int], ...]:
    targets = tuple(int(q) for q in op.get("targets", ()))
    if len(targets) % 2:
        raise ValueError(f"{op.get('name', 'operation')} has odd target count: {targets}")
    pairs: list[tuple[int, int]] = []
    for i in range(0, len(targets), 2):
        a = targets[i]
        b = targets[i + 1]
        if a == b:
            raise ValueError(f"{op.get('name', 'operation')} has repeated target pair {(a, b)}")
        pairs.append((a, b))
    return tuple(pairs)


def _eye(*, device: str):
    import torch

    return torch.eye(2, dtype=torch.complex128, device=device)


def _embed_one_qubit_operator(op, *, target_index: int, num_qubits: int, device: str):
    import torch

    n = int(num_qubits)
    target = int(target_index)
    if n < 1:
        raise ValueError("num_qubits must be positive for one-qubit operator embedding")
    if target < 0 or target >= n:
        raise ValueError(f"target_index {target} outside local support of size {n}")
    factors = []
    eye = _eye(device=device)
    local = torch.as_tensor(op, dtype=torch.complex128, device=device)
    for index in range(n):
        factors.append(local if index == target else eye)
    out = factors[0].contiguous()
    for factor in factors[1:]:
        out = torch.kron(out.contiguous(), factor.contiguous())
    return out


def _embed_two_qubit_operator(
    op,
    *,
    left_index: int,
    right_index: int,
    num_qubits: int,
    device: str,
):
    import torch

    n = int(num_qubits)
    left = int(left_index)
    right = int(right_index)
    if n < 2:
        raise ValueError("num_qubits must be at least two for two-qubit operator embedding")
    if left == right:
        raise ValueError("two-qubit operator embedding requires distinct local indices")
    if left < 0 or left >= n or right < 0 or right >= n:
        raise ValueError(
            f"local indices {(left, right)} outside local support of size {n}"
        )
    local = torch.as_tensor(op, dtype=torch.complex128, device=device)
    if tuple(local.shape) != (4, 4):
        raise ValueError(f"two-qubit operator must have shape (4, 4), got {tuple(local.shape)}")
    dim = 1 << n
    out = torch.zeros((dim, dim), dtype=torch.complex128, device=device)
    selected = {left, right}
    for row in range(dim):
        for col in range(dim):
            if any(
                _basis_bit(row, q, n) != _basis_bit(col, q, n)
                for q in range(n)
                if q not in selected
            ):
                continue
            row_local = (_basis_bit(row, left, n) << 1) | _basis_bit(row, right, n)
            col_local = (_basis_bit(col, left, n) << 1) | _basis_bit(col, right, n)
            out[row, col] = local[row_local, col_local]
    return out


def _basis_bit(index: int, qubit_index: int, num_qubits: int) -> int:
    return (int(index) >> (int(num_qubits) - 1 - int(qubit_index))) & 1


__all__ = [
    "Axis1IdealControlBundle",
    "Axis1IdealControlRecord",
    "lower_ideal_controls_for_selection",
]
