from __future__ import annotations

"""Public Axis-1 local Lindblad context metadata.

This module carries public, typed configuration for the simulator Axis-1 bridge.
It is not a Pauli/Stim noise model, not Axis-2 source truth, and not a serialized
channel payload. The values here only select/parameterize local Markovian
primitive lowering before `carrier.joint_lindbladian` assembles the joint
generator.
"""

from dataclasses import dataclass
import math
from typing import Any

from ..mechanisms.axis1_primitives import Axis1PrimitiveParams


AXIS1_LOCAL_LINDBLAD_CONTEXT_METADATA_KEY = "axis1_local_lindblad_context"
AXIS1_LOCAL_LINDBLAD_CONTEXT_SCHEMA = (
    "error_coupling_simulator.frontend.local_lindblad_context.v1"
)


@dataclass(frozen=True)
class Axis1LocalLindbladContextSpec:
    """Public Markovian context for Axis-1 primitive selection and rates."""

    include_thermal_excitation: bool = False
    gamma_up_per_ns: float = 0.0
    zeta_rad_per_ns: float | None = None
    gamma_phi_per_ns: float | None = None
    gamma_1_per_ns: float | None = None
    gamma_readout_phi_per_ns: float | None = None
    include_fsim_residual: bool = False
    fsim_delta_theta_rad: float = 0.0
    fsim_delta_phi_rad: float = 0.0
    leak_exchange_12_rad_per_ns: float = 0.0
    leak_seep_21_per_ns: float = 0.0
    leak_heat_12_per_ns: float = 0.0
    leak_exchange_11_02_rad_per_ns: float = 0.0
    leak_mobility_12_21_rad_per_ns: float = 0.0
    leak_transport_30_12_rad_per_ns: float = 0.0
    leak_transport_31_22_rad_per_ns: float = 0.0
    leak_cond_phase_left2_right_z_rad_per_ns: float = 0.0
    leak_cond_phase_left_z_right2_rad_per_ns: float = 0.0
    epistemic_class: str = "c"
    schema: str = AXIS1_LOCAL_LINDBLAD_CONTEXT_SCHEMA

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "include_thermal_excitation",
            bool(self.include_thermal_excitation),
        )
        object.__setattr__(
            self,
            "include_fsim_residual",
            bool(self.include_fsim_residual),
        )
        object.__setattr__(
            self,
            "gamma_up_per_ns",
            _nonnegative_finite("gamma_up_per_ns", self.gamma_up_per_ns),
        )
        object.__setattr__(
            self,
            "fsim_delta_theta_rad",
            _finite("fsim_delta_theta_rad", self.fsim_delta_theta_rad),
        )
        object.__setattr__(
            self,
            "fsim_delta_phi_rad",
            _finite("fsim_delta_phi_rad", self.fsim_delta_phi_rad),
        )
        for name in (
            "leak_exchange_12_rad_per_ns",
            "leak_seep_21_per_ns",
            "leak_heat_12_per_ns",
            "leak_exchange_11_02_rad_per_ns",
            "leak_mobility_12_21_rad_per_ns",
            "leak_transport_30_12_rad_per_ns",
            "leak_transport_31_22_rad_per_ns",
            "leak_cond_phase_left2_right_z_rad_per_ns",
            "leak_cond_phase_left_z_right2_rad_per_ns",
        ):
            object.__setattr__(
                self,
                name,
                _nonnegative_finite(name, getattr(self, name)),
            )
        for name in (
            "zeta_rad_per_ns",
            "gamma_phi_per_ns",
            "gamma_1_per_ns",
            "gamma_readout_phi_per_ns",
        ):
            value = getattr(self, name)
            object.__setattr__(self, name, None if value is None else _nonnegative_finite(name, value))
        if self.include_thermal_excitation and self.gamma_up_per_ns <= 0.0:
            raise ValueError(
                "include_thermal_excitation requires gamma_up_per_ns > 0"
            )
        if self.include_fsim_residual and (
            self.fsim_delta_theta_rad == 0.0 and self.fsim_delta_phi_rad == 0.0
        ):
            raise ValueError(
                "include_fsim_residual requires a nonzero fSim residual angle"
            )
        epistemic_class = str(self.epistemic_class)
        if epistemic_class not in {"a", "b", "c"}:
            raise ValueError(
                f"epistemic_class must be one of 'a', 'b', 'c', got {epistemic_class!r}"
            )
        object.__setattr__(self, "epistemic_class", epistemic_class)
        object.__setattr__(self, "schema", str(self.schema))
        if self.schema != AXIS1_LOCAL_LINDBLAD_CONTEXT_SCHEMA:
            raise ValueError(
                f"unsupported local Lindblad context schema {self.schema!r}; "
                f"expected {AXIS1_LOCAL_LINDBLAD_CONTEXT_SCHEMA!r}"
            )

    @property
    def is_trivial(self) -> bool:
        return (
            not self.include_thermal_excitation
            and self.gamma_up_per_ns == 0.0
            and self.zeta_rad_per_ns is None
            and self.gamma_phi_per_ns is None
            and self.gamma_1_per_ns is None
            and self.gamma_readout_phi_per_ns is None
            and not self.include_fsim_residual
            and self.fsim_delta_theta_rad == 0.0
            and self.fsim_delta_phi_rad == 0.0
            and self.leak_exchange_12_rad_per_ns == 0.0
            and self.leak_seep_21_per_ns == 0.0
            and self.leak_heat_12_per_ns == 0.0
            and self.leak_exchange_11_02_rad_per_ns == 0.0
            and self.leak_mobility_12_21_rad_per_ns == 0.0
            and self.leak_transport_30_12_rad_per_ns == 0.0
            and self.leak_transport_31_22_rad_per_ns == 0.0
            and self.leak_cond_phase_left2_right_z_rad_per_ns == 0.0
            and self.leak_cond_phase_left_z_right2_rad_per_ns == 0.0
        )

    @property
    def include_leakage(self) -> bool:
        return (
            self.leak_exchange_12_rad_per_ns > 0.0
            or self.leak_seep_21_per_ns > 0.0
            or self.leak_heat_12_per_ns > 0.0
            or self.leak_exchange_11_02_rad_per_ns > 0.0
            or self.leak_mobility_12_21_rad_per_ns > 0.0
            or self.leak_transport_30_12_rad_per_ns > 0.0
            or self.leak_transport_31_22_rad_per_ns > 0.0
            or self.leak_cond_phase_left2_right_z_rad_per_ns > 0.0
            or self.leak_cond_phase_left_z_right2_rad_per_ns > 0.0
        )

    def to_manifest(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "metadata_key": AXIS1_LOCAL_LINDBLAD_CONTEXT_METADATA_KEY,
            "include_thermal_excitation": self.include_thermal_excitation,
            "gamma_up_per_ns": self.gamma_up_per_ns,
            "zeta_rad_per_ns": self.zeta_rad_per_ns,
            "gamma_phi_per_ns": self.gamma_phi_per_ns,
            "gamma_1_per_ns": self.gamma_1_per_ns,
            "gamma_readout_phi_per_ns": self.gamma_readout_phi_per_ns,
            "include_fsim_residual": self.include_fsim_residual,
            "fsim_delta_theta_rad": self.fsim_delta_theta_rad,
            "fsim_delta_phi_rad": self.fsim_delta_phi_rad,
            "include_leakage": self.include_leakage,
            "leak_exchange_12_rad_per_ns": self.leak_exchange_12_rad_per_ns,
            "leak_seep_21_per_ns": self.leak_seep_21_per_ns,
            "leak_heat_12_per_ns": self.leak_heat_12_per_ns,
            "leak_exchange_11_02_rad_per_ns": self.leak_exchange_11_02_rad_per_ns,
            "leak_mobility_12_21_rad_per_ns": self.leak_mobility_12_21_rad_per_ns,
            "leak_transport_30_12_rad_per_ns": self.leak_transport_30_12_rad_per_ns,
            "leak_transport_31_22_rad_per_ns": self.leak_transport_31_22_rad_per_ns,
            "leak_cond_phase_left2_right_z_rad_per_ns": self.leak_cond_phase_left2_right_z_rad_per_ns,
            "leak_cond_phase_left_z_right2_rad_per_ns": self.leak_cond_phase_left_z_right2_rad_per_ns,
            "contains_operator_payload": False,
            "contains_serialized_channel_payload": False,
            "visibility": "public_axis1_markovian_context_not_evaluator_truth",
            "representability": (
                "public_axis1_lindblad_parameter_metadata_no_operator_matrices_no_source"
            ),
            "epistemic_class": self.epistemic_class,
            "epistemic_classes": {
                "sigma_plus_collapse_form": "a",
                "fsim_residual_hamiltonian_form": "a",
                "rate_values": self.epistemic_class,
                "thermal_excitation_selection": "c",
                "fsim_residual_angles": self.epistemic_class,
                "leak_exchange_12_rad_per_ns": self.epistemic_class,
                "leak_seep_21_per_ns": self.epistemic_class,
                "leak_heat_12_per_ns": self.epistemic_class,
                "leak_exchange_11_02_rad_per_ns": self.epistemic_class,
                "leak_mobility_12_21_rad_per_ns": self.epistemic_class,
                "leak_transport_30_12_rad_per_ns": self.epistemic_class,
                "leak_transport_31_22_rad_per_ns": self.epistemic_class,
                "leak_cond_phase_left2_right_z_rad_per_ns": self.epistemic_class,
                "leak_cond_phase_left_z_right2_rad_per_ns": self.epistemic_class,
                "leakage_selection": "c",
            },
        }

    def to_metadata(self) -> dict[str, Any]:
        if self.is_trivial:
            return {}
        return {AXIS1_LOCAL_LINDBLAD_CONTEXT_METADATA_KEY: self.to_manifest()}

    def to_axis1_primitive_params(
        self,
        defaults: Axis1PrimitiveParams,
    ) -> Axis1PrimitiveParams:
        return Axis1PrimitiveParams(
            zeta_rad_per_ns=(
                defaults.zeta_rad_per_ns
                if self.zeta_rad_per_ns is None
                else self.zeta_rad_per_ns
            ),
            gamma_phi_per_ns=(
                defaults.gamma_phi_per_ns
                if self.gamma_phi_per_ns is None
                else self.gamma_phi_per_ns
            ),
            gamma_1_per_ns=(
                defaults.gamma_1_per_ns
                if self.gamma_1_per_ns is None
                else self.gamma_1_per_ns
            ),
            gamma_up_per_ns=self.gamma_up_per_ns,
            gamma_readout_phi_per_ns=(
                defaults.gamma_readout_phi_per_ns
                if self.gamma_readout_phi_per_ns is None
                else self.gamma_readout_phi_per_ns
            ),
            drive_area_rad=defaults.drive_area_rad,
            drive_omega_rad_per_ns=defaults.drive_omega_rad_per_ns,
            fsim_delta_theta_rad=self.fsim_delta_theta_rad,
            fsim_delta_phi_rad=self.fsim_delta_phi_rad,
        )


def normalize_axis1_local_lindblad_context(raw: Any) -> Axis1LocalLindbladContextSpec:
    """Normalize public Axis-1 Lindblad metadata to a typed spec."""

    if raw in (None, {}, ()):
        return Axis1LocalLindbladContextSpec()
    if isinstance(raw, Axis1LocalLindbladContextSpec):
        return raw
    if not isinstance(raw, dict):
        raise ValueError(
            f"{AXIS1_LOCAL_LINDBLAD_CONTEXT_METADATA_KEY} must be a dict or "
            "Axis1LocalLindbladContextSpec"
        )
    payload = dict(raw)
    payload.pop("metadata_key", None)
    payload.pop("contains_operator_payload", None)
    payload.pop("contains_serialized_channel_payload", None)
    payload.pop("visibility", None)
    payload.pop("representability", None)
    payload.pop("epistemic_classes", None)
    payload.pop("include_leakage", None)
    schema = payload.get("schema", AXIS1_LOCAL_LINDBLAD_CONTEXT_SCHEMA)
    if schema != AXIS1_LOCAL_LINDBLAD_CONTEXT_SCHEMA:
        raise ValueError(
            f"unsupported Axis-1 local Lindblad context schema {schema!r}"
        )
    payload["schema"] = schema
    return Axis1LocalLindbladContextSpec(**payload)


def axis1_local_lindblad_context_from_schedule(
    schedule: Any,
) -> Axis1LocalLindbladContextSpec:
    raw = getattr(schedule, "axis1_local_lindblad_context", {})
    return normalize_axis1_local_lindblad_context(raw)


def axis1_contextual_primitive_names(
    primitive_names: tuple[str, ...],
    context: Axis1LocalLindbladContextSpec,
) -> tuple[str, ...]:
    names: list[str] = [str(name).upper() for name in primitive_names]
    if not context.include_thermal_excitation:
        return tuple(names)
    out: list[str] = []
    for name in names:
        out.append(name)
        if name == "T1" and "T1_UP" not in names and "T1_UP" not in out:
            out.append("T1_UP")
        if name == "T1_B" and "T1_UP_B" not in names and "T1_UP_B" not in out:
            out.append("T1_UP_B")
    return tuple(out)


def axis1_contextual_fsim_residual_primitives(
    context: Axis1LocalLindbladContextSpec,
) -> tuple[str, ...]:
    """Return fSim residual primitive names requested by public Axis-1 context."""

    if not context.include_fsim_residual:
        return ()
    names: list[str] = []
    if context.fsim_delta_theta_rad != 0.0:
        names.append("FSIM_SWAP")
    if context.fsim_delta_phi_rad != 0.0:
        names.append("FSIM_PHASE")
    return tuple(names)


def _finite(name: str, value: Any) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{name} must be finite, got {value!r}")
    return out


def _nonnegative_finite(name: str, value: Any) -> float:
    out = float(value)
    if not math.isfinite(out) or out < 0.0:
        raise ValueError(f"{name} must be finite and non-negative, got {value!r}")
    return out


__all__ = [
    "AXIS1_LOCAL_LINDBLAD_CONTEXT_METADATA_KEY",
    "AXIS1_LOCAL_LINDBLAD_CONTEXT_SCHEMA",
    "Axis1LocalLindbladContextSpec",
    "axis1_contextual_primitive_names",
    "axis1_contextual_fsim_residual_primitives",
    "axis1_local_lindblad_context_from_schedule",
    "normalize_axis1_local_lindblad_context",
]
