from __future__ import annotations

"""Axis-1 local mechanism primitives for joint-Lindbladian lowering.

This module owns the small physical primitive dictionary used by the simulator
Axis-1 bridge. It produces local two-qubit-window Hamiltonian terms and collapse
operators; :mod:`error_coupling_simulator.carrier.joint_lindbladian` remains
the channel assembler.
"""

from dataclasses import dataclass
import math
from typing import Any, Sequence


AXIS1_PRIMITIVE_SCHEMA = "error_coupling_simulator.mechanisms.local_primitive_bundle.v1"
AXIS1_PRIMITIVE_REGISTRY_SCHEMA = (
    "error_coupling_simulator.mechanisms.local_primitive_registry.v1"
)
AXIS1_PRIMITIVE_PARAMS_SCHEMA = (
    "error_coupling_simulator.mechanisms.local_primitive_params.v1"
)
AXIS1_TWO_QUBIT_LOCAL_REGISTRY_ID = "axis1_two_qubit_local_primitives_v1"

# NOTE: COH_* / COHERENT_PAULI_FAMILIES are intentionally NOT declared here.
# The sole canonical lowering site for coherent-generator families is
# simulator/axis1_mcwf_mps_execution._hamiltonian_matrix_for_term (via
# _embed_coherent_generator / _coherent_family_generator). This registry
# does not perform COH_* lowering; advertising it here was a
# declaration-without-lowering faithfulness trap for coherent X rotations.

SUPPORTED_AXIS1_PRIMITIVES = frozenset(
    {
        "DR",
        "ZZ",
        "T2",
        "T1",
        "T1_UP",
        "T2_B",
        "T1_B",
        "T1_UP_B",
        "RD",
        "RD_B",
        "FSIM_SWAP",
        "FSIM_PHASE",
    }
)


@dataclass(frozen=True)
class Axis1PrimitiveParams:
    """Numerical parameters for the current two-qubit Axis-1 primitive set."""

    zeta_rad_per_ns: float
    gamma_phi_per_ns: float
    gamma_1_per_ns: float
    gamma_up_per_ns: float = 0.0
    gamma_readout_phi_per_ns: float = 1.0e-3
    drive_area_rad: float = math.pi
    drive_omega_rad_per_ns: float | None = None
    fsim_delta_theta_rad: float = 0.0
    fsim_delta_phi_rad: float = 0.0
    schema: str = AXIS1_PRIMITIVE_PARAMS_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != AXIS1_PRIMITIVE_PARAMS_SCHEMA:
            raise ValueError(
                f"unsupported local-primitive parameter schema {self.schema!r}; "
                f"expected {AXIS1_PRIMITIVE_PARAMS_SCHEMA!r}"
            )
        object.__setattr__(self, "zeta_rad_per_ns", float(self.zeta_rad_per_ns))
        object.__setattr__(self, "gamma_phi_per_ns", float(self.gamma_phi_per_ns))
        object.__setattr__(self, "gamma_1_per_ns", float(self.gamma_1_per_ns))
        object.__setattr__(self, "gamma_up_per_ns", float(self.gamma_up_per_ns))
        object.__setattr__(
            self,
            "gamma_readout_phi_per_ns",
            float(self.gamma_readout_phi_per_ns),
        )
        object.__setattr__(self, "drive_area_rad", float(self.drive_area_rad))
        object.__setattr__(self, "fsim_delta_theta_rad", float(self.fsim_delta_theta_rad))
        object.__setattr__(self, "fsim_delta_phi_rad", float(self.fsim_delta_phi_rad))
        omega = (
            None
            if self.drive_omega_rad_per_ns is None
            else float(self.drive_omega_rad_per_ns)
        )
        object.__setattr__(self, "drive_omega_rad_per_ns", omega)
        if self.zeta_rad_per_ns < 0.0:
            raise ValueError("zeta_rad_per_ns must be non-negative")
        if (
            self.gamma_phi_per_ns < 0.0
            or self.gamma_1_per_ns < 0.0
            or self.gamma_up_per_ns < 0.0
            or self.gamma_readout_phi_per_ns < 0.0
        ):
            raise ValueError("gamma rates must be non-negative")
        if self.drive_area_rad <= 0.0:
            raise ValueError("drive_area_rad must be positive")
        if omega is not None and omega <= 0.0:
            raise ValueError("drive_omega_rad_per_ns must be positive when provided")
        if not math.isfinite(self.fsim_delta_theta_rad) or not math.isfinite(self.fsim_delta_phi_rad):
            raise ValueError("fSim residual angles must be finite")

    def drive_omega(self, dt_ns: float) -> float:
        if self.drive_omega_rad_per_ns is not None:
            return self.drive_omega_rad_per_ns
        dt = float(dt_ns)
        if dt <= 0.0:
            raise ValueError("dt_ns must be positive for an area-preserving drive")
        return self.drive_area_rad / dt

    def to_manifest(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "zeta_rad_per_ns": self.zeta_rad_per_ns,
            "gamma_phi_per_ns": self.gamma_phi_per_ns,
            "gamma_1_per_ns": self.gamma_1_per_ns,
            "gamma_up_per_ns": self.gamma_up_per_ns,
            "gamma_readout_phi_per_ns": self.gamma_readout_phi_per_ns,
            "drive_area_rad": self.drive_area_rad,
            "drive_omega_rad_per_ns": self.drive_omega_rad_per_ns,
            "fsim_delta_theta_rad": self.fsim_delta_theta_rad,
            "fsim_delta_phi_rad": self.fsim_delta_phi_rad,
            "epistemic_classes": {
                "zeta_rad_per_ns": "c",
                "gamma_phi_per_ns": "c",
                "gamma_1_per_ns": "c",
                "gamma_up_per_ns": "c",
                "gamma_readout_phi_per_ns": "c",
                "drive_area_or_omega": "c",
                "fsim_delta_theta_rad": "c",
                "fsim_delta_phi_rad": "c",
            },
        }


@dataclass(frozen=True)
class Axis1PrimitiveRecord:
    """JSON-safe description of one lowered primitive."""

    name: str
    generator_kind: str
    coefficient: float
    support: tuple[int, ...] = (0, 1)
    epistemic_class: str = "c"

    def __post_init__(self) -> None:
        name = str(self.name).upper()
        if name not in SUPPORTED_AXIS1_PRIMITIVES:
            raise ValueError(f"unsupported Axis-1 primitive {name!r}")
        kind = str(self.generator_kind)
        if kind not in {"hamiltonian", "collapse"}:
            raise ValueError(f"invalid generator_kind {kind!r}")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "generator_kind", kind)
        object.__setattr__(self, "coefficient", float(self.coefficient))
        object.__setattr__(self, "support", tuple(int(q) for q in self.support))
        object.__setattr__(self, "epistemic_class", str(self.epistemic_class))

    def to_manifest(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "generator_kind": self.generator_kind,
            "coefficient": self.coefficient,
            "support": list(self.support),
            "epistemic_class": self.epistemic_class,
        }


@dataclass(frozen=True)
class Axis1PrimitiveBundle:
    """Lowered two-qubit-window primitives ready for joint-L assembly."""

    primitive_names: tuple[str, ...]
    H_list: tuple[Any, ...]
    c_list: tuple[Any, ...]
    records: tuple[Axis1PrimitiveRecord, ...]
    params: Axis1PrimitiveParams
    dt_ns: float
    schema: str = AXIS1_PRIMITIVE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != AXIS1_PRIMITIVE_SCHEMA:
            raise ValueError(
                f"unsupported local-primitive bundle schema {self.schema!r}; "
                f"expected {AXIS1_PRIMITIVE_SCHEMA!r}"
            )

    def to_manifest(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "primitive_names": list(self.primitive_names),
            "num_hamiltonian_terms": len(self.H_list),
            "num_collapse_ops": len(self.c_list),
            "records": [record.to_manifest() for record in self.records],
            "params": self.params.to_manifest(),
            "dt_ns": self.dt_ns,
            "representability": "two_qubit_axis1_local_window_primitives",
            "scope": (
                "local primitive lowering only; channel assembly lives in "
                "error_coupling_simulator.carrier.joint_lindbladian"
            ),
        }


@dataclass(frozen=True)
class Axis1PrimitiveRegistry:
    """Registry contract for supported Axis-1 primitive lowering."""

    registry_id: str = AXIS1_TWO_QUBIT_LOCAL_REGISTRY_ID
    supported_primitives: tuple[str, ...] = tuple(sorted(SUPPORTED_AXIS1_PRIMITIVES))
    schema: str = AXIS1_PRIMITIVE_REGISTRY_SCHEMA

    def __post_init__(self) -> None:
        object.__setattr__(self, "registry_id", str(self.registry_id))
        names = tuple(str(name).upper() for name in self.supported_primitives)
        object.__setattr__(self, "supported_primitives", tuple(sorted(set(names))))
        object.__setattr__(self, "schema", str(self.schema))
        if self.schema != AXIS1_PRIMITIVE_REGISTRY_SCHEMA:
            raise ValueError(
                f"unsupported local-primitive registry schema {self.schema!r}; "
                f"expected {AXIS1_PRIMITIVE_REGISTRY_SCHEMA!r}"
            )
        if not self.supported_primitives:
            raise ValueError("Axis1PrimitiveRegistry requires supported primitives")

    def lower(
        self,
        primitive_names: Sequence[str],
        *,
        dt_ns: float,
        params: Axis1PrimitiveParams,
        device: str = "cuda",
    ) -> Axis1PrimitiveBundle:
        names = tuple(str(name).upper() for name in primitive_names)
        unknown = sorted(set(names) - set(self.supported_primitives))
        if unknown:
            raise ValueError(f"unsupported Axis-1 primitive(s): {unknown}")
        return lower_two_qubit_axis1_primitives(
            names,
            dt_ns=dt_ns,
            params=params,
            device=device,
        )

    def to_manifest(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "registry_id": self.registry_id,
            "supported_primitives": list(self.supported_primitives),
            "primitive_schema": AXIS1_PRIMITIVE_SCHEMA,
            "representability": "two_qubit_axis1_local_window_primitives",
            "contains_operator_payload": False,
            "scope": (
                "registry metadata and lowering entrypoint only; Hamiltonian/collapse "
                "operators are produced at runtime and not serialized here"
            ),
            "epistemic_class": "c",
        }


def default_axis1_primitive_registry() -> Axis1PrimitiveRegistry:
    """Return the current default Axis-1 primitive registry."""

    return Axis1PrimitiveRegistry()


def lower_two_qubit_axis1_primitives(
    primitive_names: Sequence[str],
    *,
    dt_ns: float,
    params: Axis1PrimitiveParams,
    device: str = "cuda",
) -> Axis1PrimitiveBundle:
    """Lower supported Axis-1 primitive names to local `H_list` and `c_list`."""

    import torch

    dt = float(dt_ns)
    if dt <= 0.0:
        raise ValueError("dt_ns must be positive for Axis-1 primitive lowering")
    names = tuple(str(name).upper() for name in primitive_names)
    unknown = sorted(set(names) - SUPPORTED_AXIS1_PRIMITIVES)
    if unknown:
        raise ValueError(f"unsupported Axis-1 primitive(s): {unknown}")

    ops = two_qubit_axis1_ops(device=device)
    H_terms: list[Any] = []
    c_ops: list[Any] = []
    records: list[Axis1PrimitiveRecord] = []
    for name in names:
        if name == "DR":
            omega = params.drive_omega(dt)
            H_terms.append((omega / 2.0) * ops["sx_a"])
            records.append(Axis1PrimitiveRecord("DR", "hamiltonian", omega / 2.0))
        elif name == "ZZ":
            H_terms.append(params.zeta_rad_per_ns * ops["n_n"])
            records.append(Axis1PrimitiveRecord("ZZ", "hamiltonian", params.zeta_rad_per_ns))
        elif name == "T2":
            coeff = math.sqrt(2.0 * params.gamma_phi_per_ns)
            c_ops.append(coeff * ops["n_a"])
            records.append(Axis1PrimitiveRecord("T2", "collapse", coeff))
        elif name == "T1":
            coeff = math.sqrt(params.gamma_1_per_ns)
            c_ops.append(coeff * ops["sm_a"])
            records.append(Axis1PrimitiveRecord("T1", "collapse", coeff))
        elif name == "T1_UP":
            coeff = math.sqrt(params.gamma_up_per_ns)
            c_ops.append(coeff * ops["sp_a"])
            records.append(Axis1PrimitiveRecord("T1_UP", "collapse", coeff))
        elif name == "T2_B":
            coeff = math.sqrt(2.0 * params.gamma_phi_per_ns)
            c_ops.append(coeff * ops["n_b"])
            records.append(Axis1PrimitiveRecord("T2_B", "collapse", coeff, support=(1,)))
        elif name == "T1_B":
            coeff = math.sqrt(params.gamma_1_per_ns)
            c_ops.append(coeff * ops["sm_b"])
            records.append(Axis1PrimitiveRecord("T1_B", "collapse", coeff, support=(1,)))
        elif name == "T1_UP_B":
            coeff = math.sqrt(params.gamma_up_per_ns)
            c_ops.append(coeff * ops["sp_b"])
            records.append(Axis1PrimitiveRecord("T1_UP_B", "collapse", coeff, support=(1,)))
        elif name == "RD":
            coeff = math.sqrt(2.0 * params.gamma_readout_phi_per_ns)
            c_ops.append(coeff * ops["n_a"])
            records.append(Axis1PrimitiveRecord("RD", "collapse", coeff))
        elif name == "RD_B":
            coeff = math.sqrt(2.0 * params.gamma_readout_phi_per_ns)
            c_ops.append(coeff * ops["n_b"])
            records.append(Axis1PrimitiveRecord("RD_B", "collapse", coeff, support=(1,)))
        elif name == "FSIM_SWAP":
            coeff = params.fsim_delta_theta_rad / dt
            H_terms.append(coeff * ops["swap_01_10"])
            records.append(Axis1PrimitiveRecord("FSIM_SWAP", "hamiltonian", coeff))
        elif name == "FSIM_PHASE":
            coeff = params.fsim_delta_phi_rad / dt
            H_terms.append(coeff * ops["n_n"])
            records.append(Axis1PrimitiveRecord("FSIM_PHASE", "hamiltonian", coeff))
    # Keep tensors as tensors while making the type checker happy about the local import.
    H_tuple = tuple(torch.as_tensor(term, device=device) for term in H_terms)
    c_tuple = tuple(torch.as_tensor(op, device=device) for op in c_ops)
    return Axis1PrimitiveBundle(
        primitive_names=names,
        H_list=H_tuple,
        c_list=c_tuple,
        records=tuple(records),
        params=params,
        dt_ns=dt,
    )


def two_qubit_axis1_ops(*, device: str = "cuda") -> dict[str, Any]:
    """Return local two-qubit-window operators used by the current primitives."""

    import torch

    dev = str(device)
    if not dev.startswith("cuda"):
        raise ValueError(
            "Axis-1 primitive lowering is GPU-only; pass device='cuda' and run on the workstation"
        )
    cdt = torch.complex128
    eye = torch.eye(2, dtype=cdt, device=dev)
    sx = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=dev)
    n = torch.tensor([[0.0, 0.0], [0.0, 1.0]], dtype=cdt, device=dev)
    sm = torch.tensor([[0.0, 1.0], [0.0, 0.0]], dtype=cdt, device=dev)
    sp = torch.tensor([[0.0, 0.0], [1.0, 0.0]], dtype=cdt, device=dev)
    swap_01_10 = torch.zeros((4, 4), dtype=cdt, device=dev)
    swap_01_10[1, 2] = 1.0
    swap_01_10[2, 1] = 1.0
    return {
        "sx_a": torch.kron(sx, eye),
        "n_n": torch.kron(n, n),
        "n_a": torch.kron(n, eye),
        "sm_a": torch.kron(sm, eye),
        "sp_a": torch.kron(sp, eye),
        "n_b": torch.kron(eye, n),
        "sm_b": torch.kron(eye, sm),
        "sp_b": torch.kron(eye, sp),
        "swap_01_10": swap_01_10,
    }


__all__ = [
    "AXIS1_PRIMITIVE_SCHEMA",
    "AXIS1_PRIMITIVE_REGISTRY_SCHEMA",
    "AXIS1_TWO_QUBIT_LOCAL_REGISTRY_ID",
    "SUPPORTED_AXIS1_PRIMITIVES",
    "Axis1PrimitiveBundle",
    "Axis1PrimitiveParams",
    "Axis1PrimitiveRecord",
    "Axis1PrimitiveRegistry",
    "default_axis1_primitive_registry",
    "lower_two_qubit_axis1_primitives",
    "two_qubit_axis1_ops",
]
