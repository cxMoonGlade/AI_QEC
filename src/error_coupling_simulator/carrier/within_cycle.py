"""Package-local within-cycle qutrit schedule and WG leakage host.

This module consumes an already compiled schedule.  Parsing a hardware dataset is a
frontend responsibility; the carrier never discovers or substitutes a circuit on its
own. The implementation owns the within-cycle host interface used by the PEPS carrier.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, field, replace
from functools import lru_cache
from importlib import metadata
from pathlib import Path
from typing import Any

import numpy as np
import torch

from ..mechanisms.qutrit_leakage import (
    _super_to_kraus,
    leakage_channel_super,
    leakage_kraus,
)
from .records import (
    PACKED_DETECTOR_INITIAL_PRIOR,
    PACKED_SHOT_SCHEMA,
    PACKED_SYNDROME_LAYOUT,
    PackedShotBatch,
    RecordBatch,
)

CDTYPE = torch.complex128
CPTP_TOL = 1e-12
WC_LEAK_COMPOSE_TOL = 1e-12
WC_LEAK_FRAC = 0.25
CODESTATE_TOL = 1e-10

SV_GATE_IDS: dict[str, int] = {
    "I": 0,
    "H": 1,
    "X": 2,
    "Y": 3,
    "S": 4,
    "S_DAG": 5,
}
SV_GATE_NAMES: tuple[str, ...] = tuple(
    name for name, _ in sorted(SV_GATE_IDS.items(), key=lambda item: item[1])
)
SV_ARMS: tuple[str, ...] = ("A", "C", "B1", "B2")
SV_READOUT_CONVENTIONS: tuple[str, ...] = ("biased_b", "half")
SV_ARM_CODE: dict[str, int] = {"A": 0, "C": 1, "B1": 2, "B2": 3}
SV_READOUT_CODE: dict[str, int] = {"biased_b": 0, "half": 1}
WC_OP_GATE = 0
WC_OP_LEAK = 1

RUN_PURPOSES: tuple[str, ...] = ("optimization", "final", "certification")
PRECISION_POLICY = "optimization_c64_final_certification_c128_v1"
_RUN_PURPOSE_DTYPE: dict[str, str] = {
    "optimization": "c64",
    "final": "c128",
    "certification": "c128",
}
_RUN_PURPOSE_EVIDENCE: dict[str, str] = {
    "optimization": "screening_only",
    "final": "c128_candidate",
    "certification": "c128_candidate",
}

_RUN_NUMERICAL_PROVENANCE_SCHEMA = (
    "error_coupling_simulator.frontend.run_numerical_provenance.v1"
)
_PRESET_NUMERICAL_PROVENANCE_SCHEMA = (
    "error_coupling_simulator.frontend.experiment_preset_provenance.v1"
)
_PACKAGE_BUILD_IDENTITY_SCHEMA = (
    "error_coupling_simulator.carrier.package_build_identity.v1"
)

__all__ = [
    "CPTP_TOL",
    "CODESTATE_TOL",
    "FusedWithinCycleSampler",
    "PRECISION_POLICY",
    "RUN_PURPOSES",
    "RunSpec",
    "SV_ARMS",
    "SV_ARM_CODE",
    "SV_GATE_IDS",
    "SV_GATE_NAMES",
    "SV_READOUT_CODE",
    "SV_READOUT_CONVENTIONS",
    "WC_LEAK_COMPOSE_TOL",
    "WC_LEAK_FRAC",
    "WC_OP_GATE",
    "WC_OP_LEAK",
    "WithinCycleMarshalled",
    "WithinCycleScheduleHost",
    "cast_within_cycle_precision",
    "c128_evidence_record_batch",
    "package_build_identity",
    "require_c128_evidence_header",
    "run_dtype_for_purpose",
    "run_evidence_eligibility",
]


def run_dtype_for_purpose(purpose: str) -> str:
    """The only allowed compute dtype for a declared run purpose."""
    key = str(purpose)
    try:
        return _RUN_PURPOSE_DTYPE[key]
    except KeyError as exc:
        raise ValueError(
            f"run_purpose must be one of {RUN_PURPOSES} (got {purpose!r})"
        ) from exc


def run_evidence_eligibility(purpose: str) -> str:
    """Artifact role implied by ``purpose``; this never asserts a gate passed."""
    key = str(purpose)
    try:
        return _RUN_PURPOSE_EVIDENCE[key]
    except KeyError as exc:
        raise ValueError(
            f"run_purpose must be one of {RUN_PURPOSES} (got {purpose!r})"
        ) from exc


def _torch_complex_dtype(dtype: str) -> torch.dtype:
    if str(dtype) == "c128":
        return torch.complex128
    if str(dtype) == "c64":
        return torch.complex64
    raise ValueError(f"dtype must be 'c128' or 'c64' (got {dtype!r})")


def _validate_run_numerical_provenance(
    payload: dict[str, Any], spec: Any, *, allow_complete: bool = False,
) -> None:
    """Fail closed on malformed, inconsistent, or self-promoting provenance."""
    if payload.get("schema") != _RUN_NUMERICAL_PROVENANCE_SCHEMA:
        raise ValueError("numerical_provenance has an invalid run schema")
    status = payload.get("status")
    if status not in {"missing", "complete_for_registered_preset"}:
        raise ValueError("numerical_provenance has an invalid status")
    if status == "complete_for_registered_preset" and not allow_complete:
        raise ValueError(
            "complete numerical_provenance is accepted only from the registered facade")
    binding = payload.get("run_binding")
    if not isinstance(binding, dict):
        raise ValueError("numerical_provenance.run_binding must be an object")
    resolved = binding.get("resolved_theta_rad")
    dataset = binding.get("dataset_files")
    shape = binding.get("run_shape")
    precision = binding.get("precision")
    if not all(
        isinstance(item, dict) for item in (resolved, dataset, shape, precision)
    ):
        raise ValueError("numerical_provenance run-binding sections must be objects")

    expected_binding = {
        "theta": float(spec.theta),
        "circuit": str(spec.circuit_path),
        "metadata": None if spec.metadata_path is None else str(spec.metadata_path),
        "N": int(spec.N),
        "R": None if spec.R is None else int(spec.R),
        "seed": int(spec.base_seed),
        "m": int(spec.m),
        "precision_policy": PRECISION_POLICY,
        "run_purpose": str(spec.run_purpose),
        "dtype": str(spec.dtype),
        "evidence_eligibility": str(spec.evidence_eligibility),
    }
    actual_binding = {
        "theta": resolved.get("value"),
        "circuit": dataset.get("circuit"),
        "metadata": dataset.get("metadata"),
        "N": shape.get("n_shots"),
        "R": shape.get("n_rounds"),
        "seed": shape.get("seed"),
        "m": shape.get("logical_input_m"),
        "precision_policy": precision.get("policy"),
        "run_purpose": precision.get("run_purpose"),
        "dtype": precision.get("dtype"),
        "evidence_eligibility": precision.get("evidence_eligibility"),
    }
    if actual_binding != expected_binding:
        raise ValueError("numerical_provenance run binding does not match RunSpec")
    if (
        resolved.get("claims_device_calibration") is not False
        or dataset.get("supplies_physical_noise_parameters") is not False
    ):
        raise ValueError("numerical_provenance may not claim device calibration")

    if status == "missing":
        if payload.get("claim_scope") != "implementation_only":
            raise ValueError(
                "missing provenance must fail closed to implementation_only")
        if "preset_manifest" in payload or "preset_manifest_sha256" in payload:
            raise ValueError("missing provenance may not carry a trusted preset manifest")
        return

    manifest = payload.get("preset_manifest")
    digest = payload.get("preset_manifest_sha256")
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema") != _PRESET_NUMERICAL_PROVENANCE_SCHEMA
    ):
        raise ValueError("complete provenance requires a v1 preset manifest")
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    if (
        not isinstance(digest, str)
        or hashlib.sha256(canonical.encode("utf-8")).hexdigest() != digest
    ):
        raise ValueError("complete provenance preset-manifest digest mismatch")
    fields = manifest.get("fields")
    whole = manifest.get("whole_preset")
    if not isinstance(fields, dict) or not isinstance(whole, dict):
        raise ValueError("complete provenance manifest sections are missing")
    expected_values = {
        "g_seep": float(spec.g_seep),
        "g_heat": float(spec.g_heat),
        "b_bias": float(spec.b),
        "arm": str(spec.arm),
        "readout_conv": str(spec.readout_conv),
    }
    for field_name, expected in expected_values.items():
        entry = fields.get(field_name)
        if not isinstance(entry, dict) or entry.get("value") != expected:
            raise ValueError(
                f"complete provenance field {field_name} does not match RunSpec")
    theta_entry = fields.get("theta_rad")
    target_entry = fields.get("wg_l1_target")
    if not isinstance(theta_entry, dict) or not isinstance(target_entry, dict):
        raise ValueError("complete provenance theta convention is missing")
    if theta_entry.get("value") is not None:
        if float(theta_entry["value"]) != float(spec.theta):
            raise ValueError("complete provenance raw theta does not match RunSpec")
    elif target_entry.get("value") is None:
        raise ValueError("complete provenance has no theta convention")
    if (
        whole.get("physical_cell_validated_by_literature") is not False
        or whole.get("direct_whole_cell_literature_support_count") != 0
    ):
        raise ValueError("complete provenance overclaims whole-cell literature support")
    if payload.get("claim_scope") != (
        "registered_synthetic_cross_source_benchmark_only"
    ):
        raise ValueError("complete provenance has an invalid claim scope")


@dataclass(frozen=True)
class RunSpec:
    """One explicit within-cycle carrier run specification.

    ``dtype`` is derived from ``run_purpose`` when omitted.  Supplying both is
    allowed only when they match the binding precision policy.
    """

    circuit_path: str | Path
    metadata_path: str | Path | None = None
    sweep_word: dict[int, int] | None = None
    m: int = 0
    theta: float = 0.0
    g_seep: float = 0.0
    g_heat: float = 0.0
    arm: str = "A"
    b: float = 1.0
    readout_conv: str = "biased_b"
    N: int = 1000
    base_seed: int = 0
    W: int = 1024
    R: int | None = None
    dtype: str | None = None
    run_purpose: str = "final"
    out_path: str | Path | None = None
    numerical_provenance: dict[str, Any] | None = None
    _numerical_provenance_json: str | None = field(
        default=None, init=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        if int(self.m) not in (0, 1):
            raise ValueError(f"logical m must be 0 or 1 (got {self.m})")
        if str(self.arm).upper() not in SV_ARMS:
            raise ValueError(f"arm must be one of {SV_ARMS} (got {self.arm!r})")
        if str(self.readout_conv) not in SV_READOUT_CONVENTIONS:
            raise ValueError(
                "readout_conv must be one of "
                f"{SV_READOUT_CONVENTIONS} (got {self.readout_conv!r})")
        dtype = None if self.dtype is None else str(self.dtype)
        if dtype not in (None, "c128", "c64"):
            raise ValueError(
                f"dtype must be 'c128' or 'c64' (got {self.dtype!r})")
        purpose = str(self.run_purpose)
        expected_dtype = run_dtype_for_purpose(purpose)
        if dtype is None:
            dtype = expected_dtype
            object.__setattr__(self, "dtype", dtype)
        elif dtype != expected_dtype:
            raise ValueError(
                f"precision policy {PRECISION_POLICY}: run_purpose={purpose!r} "
                f"requires dtype={expected_dtype!r} (got {self.dtype!r})")
        if not 0.0 <= float(self.b) <= 1.0:
            raise ValueError(f"readout bias b must be in [0,1] (got {self.b})")
        if int(self.N) < 1 or int(self.W) < 1:
            raise ValueError("N and W must be >= 1")
        if self.numerical_provenance is not None:
            try:
                canonical = json.loads(json.dumps(
                    self.numerical_provenance, sort_keys=True))
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "numerical_provenance must be JSON-safe") from exc
            _validate_run_numerical_provenance(canonical, self)
            object.__setattr__(self, "numerical_provenance", canonical)
            object.__setattr__(
                self,
                "_numerical_provenance_json",
                json.dumps(canonical, sort_keys=True, separators=(",", ":")),
            )

    @property
    def evidence_eligibility(self) -> str:
        """Whether the artifact may enter an evidence pipeline.

        ``c128_candidate`` still means candidate only; no numerical gate is
        declared passed by constructing a :class:`RunSpec`.
        """
        return run_evidence_eligibility(str(self.run_purpose))


def _bind_registered_numerical_provenance(
    spec: RunSpec, payload: dict[str, Any],
) -> RunSpec:
    """Bind a complete manifest through the registered experiment facade seam."""
    if (
        spec.numerical_provenance is not None
        or spec._numerical_provenance_json is not None
    ):
        raise ValueError("RunSpec already carries numerical provenance")
    try:
        canonical = json.loads(json.dumps(payload, sort_keys=True))
    except (TypeError, ValueError) as exc:
        raise ValueError("numerical_provenance must be JSON-safe") from exc
    _validate_run_numerical_provenance(canonical, spec, allow_complete=True)
    object.__setattr__(spec, "numerical_provenance", canonical)
    object.__setattr__(
        spec,
        "_numerical_provenance_json",
        json.dumps(canonical, sort_keys=True, separators=(",", ":")),
    )
    return spec


@dataclass(frozen=True)
class WithinCycleMarshalled:
    """Flat device arrays for the per-qutrit gate/leak stream."""

    n_data: int
    n_stab: int
    R: int
    round_op_ptr: torch.Tensor
    op_kind: torch.Tensor
    op_uid: torch.Tensor
    op_site: torch.Tensor
    stab_supp: torch.Tensor
    stab_supp_isx: torch.Tensor
    stab_supp_len: torch.Tensor
    log_supp: torch.Tensor
    log_supp_isx: torch.Tensor
    logical_kind: int
    leak_kraus: torch.Tensor
    gate_unitaries: torch.Tensor
    w_max: int = 0
    gate_names: tuple[str, ...] = SV_GATE_NAMES
    streams_by_pos: dict[int, tuple[str, ...]] = field(default_factory=dict)
    n_cz_by_pos: dict[int, int] = field(default_factory=dict)


def cast_within_cycle_precision(
    marshalled: WithinCycleMarshalled, dtype: str,
) -> WithinCycleMarshalled:
    """Cast only the complex kernel tables after c128 physics certification.

    Schedule/index arrays remain the exact same int32 tensor objects.  The WG
    channel is always constructed and checked in c128 by
    :meth:`WithinCycleScheduleHost.build_within_cycle_leak`; this is only the
    execution-ABI cast for the fused optimization kernel.
    """
    target = _torch_complex_dtype(dtype)
    return replace(
        marshalled,
        leak_kraus=marshalled.leak_kraus.to(dtype=target).contiguous(),
        gate_unitaries=marshalled.gate_unitaries.to(dtype=target).contiguous(),
    )


def require_c128_evidence_header(header: dict[str, Any]) -> None:
    """Fail closed before a shot artifact enters final/certification evidence."""
    policy = header.get("precision_policy")
    purpose = header.get("run_purpose")
    dtype = header.get("dtype")
    eligibility = header.get("evidence_eligibility")
    if (
        policy != PRECISION_POLICY
        or purpose not in {"final", "certification"}
        or dtype != "c128"
        or eligibility != "c128_candidate"
    ):
        raise ValueError(
            f"c128 evidence requires precision_policy {PRECISION_POLICY!r}, "
            "run_purpose final/certification, dtype c128, and "
            "evidence_eligibility c128_candidate")
    _require_package_build_identity(header.get("build_identity"))


def _require_package_build_identity(identity: Any) -> None:
    """Validate the install-portable code identity carried by evidence headers."""
    if not isinstance(identity, dict):
        raise ValueError("c128 evidence requires a build_identity object")
    expected = {
        "schema": _PACKAGE_BUILD_IDENTITY_SCHEMA,
        "distribution": "error-coupling-simulator",
    }
    for key, value in expected.items():
        if identity.get(key) != value:
            raise ValueError(
                f"c128 evidence build_identity.{key} must be {value!r}")
    version_value = identity.get("version")
    digest = identity.get("package_tree_sha256")
    revision = identity.get("git_commit")
    if not isinstance(version_value, str) or not version_value:
        raise ValueError("c128 evidence build_identity.version is missing")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError(
            "c128 evidence build_identity.package_tree_sha256 must be a sha256")
    try:
        int(digest, 16)
    except ValueError as exc:
        raise ValueError(
            "c128 evidence build_identity.package_tree_sha256 must be hexadecimal"
        ) from exc
    if revision is not None and (not isinstance(revision, str) or not revision):
        raise ValueError(
            "c128 evidence build_identity.git_commit must be null or non-empty")


def c128_evidence_record_batch(
    batch: PackedShotBatch, *, expected_purpose: str,
) -> RecordBatch:
    """Cross the final/certification boundary without losing precision metadata.

    Ordinary optimization code may call :meth:`PackedShotBatch.to_record_batch`
    directly.  Evidence consumers must use this helper before reducing a batch to
    bare detector/observable arrays, because that reduction no longer carries the
    self-describing header.
    """
    if not isinstance(batch, PackedShotBatch):
        raise TypeError("batch must be a PackedShotBatch")
    if expected_purpose not in {"final", "certification"}:
        raise ValueError(
            "expected_purpose must be 'final' or 'certification' "
            f"(got {expected_purpose!r})")
    require_c128_evidence_header(dict(batch.header))
    actual = batch.header.get("run_purpose")
    if actual != expected_purpose:
        raise ValueError(
            "evidence run-purpose mismatch: "
            f"expected {expected_purpose!r}, header has {actual!r}")
    return batch.to_record_batch()


def _qutrit_gate(name: str, device: torch.device) -> torch.Tensor:
    """Local qutrit gate formula; the leaked level is inert."""
    gate = str(name).upper()
    matrix = torch.zeros((3, 3), dtype=CDTYPE, device=device)
    if gate == "I":
        return torch.eye(3, dtype=CDTYPE, device=device)
    if gate == "H":
        inv_sqrt_two = 1.0 / (2.0 ** 0.5)
        matrix[0, 0] = inv_sqrt_two
        matrix[0, 1] = inv_sqrt_two
        matrix[1, 0] = inv_sqrt_two
        matrix[1, 1] = -inv_sqrt_two
    elif gate == "X":
        matrix[0, 1] = 1.0
        matrix[1, 0] = 1.0
    elif gate == "Y":
        matrix[0, 1] = -1.0j
        matrix[1, 0] = 1.0j
    elif gate == "S":
        matrix[0, 0] = 1.0
        matrix[1, 1] = 1.0j
    elif gate == "S_DAG":
        matrix[0, 0] = 1.0
        matrix[1, 1] = -1.0j
    else:
        raise ValueError(f"unsupported gate {name!r} (known: {SV_GATE_NAMES})")
    matrix[2, 2] = 1.0
    return matrix


def _gate_unitaries_table(device: torch.device) -> torch.Tensor:
    return torch.stack([
        _qutrit_gate(name, device) for name in SV_GATE_NAMES
    ]).contiguous()


def _torch_kraus(
    kraus: list[np.ndarray], device: torch.device,
) -> torch.Tensor:
    return torch.stack([
        torch.as_tensor(item, dtype=CDTYPE, device=device) for item in kraus
    ]).contiguous()


class WithinCycleScheduleHost:
    """WG leak builder plus structural within-cycle schedule marshaller."""

    def __init__(self, device: str | torch.device = "cuda") -> None:
        self.device = torch.device(device)

    @staticmethod
    def cptp_residual(kraus: torch.Tensor) -> float:
        dimension = kraus.shape[-1]
        accumulated = torch.einsum("kab,kac->bc", kraus.conj(), kraus)
        identity = torch.eye(
            dimension, dtype=accumulated.dtype, device=accumulated.device)
        return float(torch.max(torch.abs(accumulated - identity)).real)

    def build_within_cycle_leak(
        self, spec: RunSpec,
    ) -> tuple[torch.Tensor, dict[str, Any]]:
        if self.device.type != "cuda":
            raise RuntimeError(
                "GPU-only within-cycle physics: host device must be cuda "
                f"(got {self.device})")
        if not torch.cuda.is_available():
            raise RuntimeError(
                "GPU-only within-cycle physics: CUDA must be available")
        slice_super = leakage_channel_super(
            spec.theta,
            spec.g_seep,
            spec.g_heat,
            t=WC_LEAK_FRAC,
        )
        leak = _torch_kraus(_super_to_kraus(slice_super), self.device)
        cptp = self.cptp_residual(leak)
        if cptp >= CPTP_TOL:
            raise AssertionError(
                "within-cycle leak slice exp(L/4) CPTP residual "
                f"{cptp:.3e} >= {CPTP_TOL:.0e} "
                f"(theta={spec.theta}, g_seep={spec.g_seep}, "
                f"g_heat={spec.g_heat})")
        compose = self._leak_compose_residual(spec, leak)
        if compose >= WC_LEAK_COMPOSE_TOL:
            raise AssertionError(
                "within-cycle leak composition "
                f"|exp(L)(rho1) - exp(L/4)^4(rho1)| = {compose:.3e} "
                f">= {WC_LEAK_COMPOSE_TOL:.0e}")
        return leak, {
            "frac": WC_LEAK_FRAC,
            "n_kraus_slice": int(leak.shape[0]),
            "cptp_residual": cptp,
            "compose_residual": compose,
            "theta": float(spec.theta),
            "g_seep": float(spec.g_seep),
            "g_heat": float(spec.g_heat),
        }

    def _leak_compose_residual(
        self, spec: RunSpec, leak: torch.Tensor,
    ) -> float:
        full = _torch_kraus(
            leakage_kraus(spec.theta, spec.g_seep, spec.g_heat), self.device)
        rho = torch.zeros((3, 3), dtype=CDTYPE, device=self.device)
        rho[1, 1] = 1.0
        full_output = torch.einsum(
            "kab,bc,kdc->ad", full, rho, full.conj())
        composed = rho
        for _ in range(4):
            composed = torch.einsum(
                "kab,bc,kdc->ad", leak, composed, leak.conj())
        return float(torch.max(torch.abs(full_output - composed)).real)

    def marshal_within_cycle(
        self,
        schedule: Any,
        leak_kraus: torch.Tensor,
        *,
        R: int | None = None,
    ) -> WithinCycleMarshalled:
        streams = list(schedule.within_cycle_streams)
        n_data = int(schedule.n_data)
        n_stab = len(schedule.stabilizers)
        rounds = int(schedule.rounds if R is None else R)
        if rounds < 1:
            raise ValueError(f"R must be >= 1 (got {rounds})")
        if not streams:
            raise ValueError(
                "marshal_within_cycle requires explicit within-cycle streams; "
                "compile or load them in the frontend before invoking the carrier")
        if len(streams) != n_data:
            raise AssertionError(
                f"within-cycle streams count {len(streams)} != n_data {n_data}")
        by_position = {stream.pos: stream for stream in streams}
        if sorted(by_position) != list(range(n_data)):
            raise AssertionError(
                "within-cycle stream positions "
                f"{sorted(by_position)} != 0..{n_data - 1}")

        stabilizers = schedule.stab_paulis()
        if len(stabilizers) != n_stab:
            raise AssertionError(
                f"stab_paulis() count {len(stabilizers)} != n_stab {n_stab}")
        max_weight = max((len(paulis) for paulis in stabilizers), default=0)
        stab_supp = np.zeros((n_stab, max_weight), dtype=np.int32)
        stab_supp_isx = np.zeros((n_stab, max_weight), dtype=np.int32)
        stab_supp_len = np.zeros((n_stab,), dtype=np.int32)
        for stab_index, paulis in enumerate(stabilizers):
            sites = sorted(paulis)
            stab_supp_len[stab_index] = len(sites)
            for offset, site in enumerate(sites):
                pauli = str(paulis[site]).upper()
                if pauli not in ("X", "Z"):
                    raise ValueError(
                        f"stab {stab_index} site {site}: non-X/Z pauli {pauli!r}")
                stab_supp[stab_index, offset] = int(site)
                stab_supp_isx[stab_index, offset] = int(pauli == "X")

        logical_sites = sorted(schedule.logical)
        log_supp = np.asarray(logical_sites, dtype=np.int32)
        log_supp_isx = np.asarray([
            int(str(schedule.logical[site]).upper() == "X")
            for site in logical_sites
        ], dtype=np.int32)
        logical_kind = int(str(schedule.logical_kind).upper() != "X")

        round_op_ptr = [0]
        op_kind: list[int] = []
        op_uid: list[int] = []
        op_site: list[int] = []

        def emit_gate(gate_id: int, site: int) -> None:
            op_kind.append(WC_OP_GATE)
            op_uid.append(gate_id)
            op_site.append(site)

        def emit_leak(site: int) -> None:
            op_kind.append(WC_OP_LEAK)
            op_uid.append(0)
            op_site.append(site)

        for round_index in range(rounds):
            terminal = round_index == rounds - 1
            for position in range(n_data):
                for token in by_position[position].pre_measure_tokens():
                    if token in ("H", "X"):
                        emit_gate(SV_GATE_IDS[token], position)
                    elif token == "LEAK":
                        emit_leak(position)
                    else:
                        raise AssertionError(
                            f"within-cycle pos {position}: unexpected pre-M "
                            f"token {token!r}")
            round_op_ptr.append(len(op_kind))
            if not terminal:
                for position in range(n_data):
                    for token in by_position[position].post_measure_tokens():
                        if token != "Y":
                            raise AssertionError(
                                f"within-cycle pos {position}: unexpected post-M "
                                f"token {token!r}")
                        emit_gate(SV_GATE_IDS["Y"], position)
            round_op_ptr.append(len(op_kind))

        def int32_tensor(values: Any) -> torch.Tensor:
            return torch.as_tensor(
                np.asarray(values, dtype=np.int32),
                dtype=torch.int32,
                device=self.device,
            ).contiguous()

        return WithinCycleMarshalled(
            n_data=n_data,
            n_stab=n_stab,
            R=rounds,
            round_op_ptr=int32_tensor(round_op_ptr),
            op_kind=int32_tensor(op_kind),
            op_uid=int32_tensor(op_uid),
            op_site=int32_tensor(op_site),
            stab_supp=int32_tensor(stab_supp),
            stab_supp_isx=int32_tensor(stab_supp_isx),
            stab_supp_len=int32_tensor(stab_supp_len),
            log_supp=int32_tensor(log_supp),
            log_supp_isx=int32_tensor(log_supp_isx),
            logical_kind=logical_kind,
            leak_kraus=leak_kraus.to(self.device).contiguous(),
            gate_unitaries=_gate_unitaries_table(self.device),
            w_max=max_weight,
            streams_by_pos={
                position: tuple(by_position[position].tokens)
                for position in range(n_data)
            },
            n_cz_by_pos={
                position: int(by_position[position].n_cz)
                for position in range(n_data)
            },
        )

    @staticmethod
    def syndrome_bits_per_shot(n_stab: int, rounds: int) -> int:
        return int(n_stab) * int(rounds)

    def build_header(
        self, spec: RunSpec, marshalled: WithinCycleMarshalled, schedule: Any,
    ) -> dict[str, Any]:
        expected_dtype = _torch_complex_dtype(spec.dtype)
        actual = {
            "leak_kraus": marshalled.leak_kraus.dtype,
            "gate_unitaries": marshalled.gate_unitaries.dtype,
        }
        mismatch = {
            name: dtype for name, dtype in actual.items()
            if dtype != expected_dtype
        }
        if mismatch:
            raise ValueError(
                "shot header precision would not match marshalled tensor dtype: "
                f"spec={spec.dtype!r}, expected={expected_dtype}, actual={mismatch}; "
                "use cast_within_cycle_precision after c128 certification")
        bits = self.syndrome_bits_per_shot(
            marshalled.n_stab, marshalled.R)
        build_identity = package_build_identity()
        header: dict[str, Any] = {
            "format": PACKED_SHOT_SCHEMA,
            "n_data": marshalled.n_data,
            "n_stab": marshalled.n_stab,
            "R": marshalled.R,
            "N": int(spec.N),
            "m": int(spec.m),
            "arm": str(spec.arm).upper(),
            "arm_code": SV_ARM_CODE[str(spec.arm).upper()],
            "b": float(spec.b),
            "readout_conv": str(spec.readout_conv),
            "readout_conv_code": SV_READOUT_CODE[str(spec.readout_conv)],
            "theta": float(spec.theta),
            "g_seep": float(spec.g_seep),
            "g_heat": float(spec.g_heat),
            "base_seed": int(spec.base_seed),
            "wave": int(spec.W),
            "dtype": str(spec.dtype),
            "run_purpose": str(spec.run_purpose),
            "evidence_eligibility": str(spec.evidence_eligibility),
            "precision_policy": PRECISION_POLICY,
            "logical_kind": str(schedule.logical_kind).upper(),
            "logical_support": [
                int(value) for value in marshalled.log_supp.tolist()
            ],
            "syndrome_bits_per_shot": bits,
            "out_stride_bytes": (bits + 7) // 8 + 1,
            "syndrome_layout": PACKED_SYNDROME_LAYOUT,
            "detector_initial_prior": PACKED_DETECTOR_INITIAL_PRIOR,
            "build_identity": dict(build_identity),
            "package_version": build_identity["version"],
            "package_tree_sha256": build_identity["package_tree_sha256"],
            # Retained as an optional convenience field. Installed wheels are
            # identified by the mandatory package-tree digest even without Git.
            "git_commit": build_identity["git_commit"] or "",
            "source_circuit": str(spec.circuit_path),
            "gate_ids": dict(SV_GATE_IDS),
        }
        if spec._numerical_provenance_json is not None:
            header["numerical_provenance"] = json.loads(
                spec._numerical_provenance_json)
        return header


class FusedWithinCycleSampler(WithinCycleScheduleHost):
    """Active fused-SV execution owner for the circuit-faithful d3 carrier.

    The frontend must supply an explicit compiled schedule.  Physics objects and the
    logical codestate are constructed and checked in complex128.  Only after those
    checks does an ``optimization`` run cast its execution tensors to complex64;
    ``final`` and ``certification`` remain complex128 by :class:`RunSpec` contract.
    """

    _N_DATA = 9
    _STATE_DIM = 3 ** _N_DATA

    def build_codestate(
        self, schedule: Any, logical_m: int,
    ) -> tuple[torch.Tensor, dict[str, Any]]:
        """Build and verify ``|logical_m>_L`` in complex128 before execution.

        This package-local check uses the exact qutrit engine only as a state-vector
        constructor/operator reference;
        no full density matrix is materialized.
        """
        if self.device.type != "cuda":
            raise RuntimeError(
                "GPU-only fused-SV codestate build requires a cuda device "
                f"(got {self.device})")
        if not torch.cuda.is_available():
            raise RuntimeError(
                "GPU-only fused-SV codestate build requires CUDA")
        if int(schedule.n_data) != self._N_DATA:
            raise ValueError(
                "the fused sv_traj_d3_wc kernel is specialized to 9 data qutrits "
                f"(got {schedule.n_data})")
        m = int(logical_m)
        if m not in (0, 1):
            raise ValueError(f"logical m must be 0 or 1 (got {logical_m})")

        from .exact.qutrit_dm import QutritDM

        stabilizers = schedule.stab_paulis()
        logical = dict(schedule.logical)
        logical_kind = str(schedule.logical_kind).upper()
        engine = QutritDM(self._N_DATA, device=self.device)
        engine.set_code(
            stabilizers=stabilizers,
            logical_z=logical if logical_kind == "Z" else None,
            logical_x=logical if logical_kind == "X" else None,
        )
        psi = engine._codestate_vector(m)  # state-vector only; no full DM
        norm = torch.linalg.vector_norm(psi)
        if float(norm.real) <= 1e-12:
            raise RuntimeError(
                f"codestate |{m}>_L collapsed to zero norm; code geometry is "
                "inconsistent")
        psi = (psi / norm.to(CDTYPE)).contiguous()

        def expectation(paulis: dict[int, str]) -> float:
            operated = engine._apply_logical_vector(psi.clone(), paulis)
            return float(torch.vdot(psi, operated).real)

        stabilizer_values = [expectation(item) for item in stabilizers]
        logical_value = expectation(logical)
        logical_target = float((-1) ** m)
        worst_stabilizer = max(
            (abs(value - 1.0) for value in stabilizer_values), default=0.0)
        worst_logical = abs(logical_value - logical_target)
        worst = max(worst_stabilizer, worst_logical)
        if worst >= CODESTATE_TOL:
            raise AssertionError(
                f"codestate |{m}>_L check failed: max|<S>-1|="
                f"{worst_stabilizer:.2e}, |<L>-(-1)^m|="
                f"{worst_logical:.2e} (tol {CODESTATE_TOL:.0e})")
        return psi, {
            "m": m,
            "stab_expectations": stabilizer_values,
            "logical_expectation": logical_value,
            "logical_target": logical_target,
            "worst_S_residual": worst_stabilizer,
            "worst_L_residual": worst_logical,
            "norm": float(norm.real),
            "construction_dtype": "c128",
        }

    def sample(
        self,
        spec: RunSpec,
        *,
        schedule: Any,
        materialize: bool = True,
        urandom: torch.Tensor | None = None,
        urandom_stride: int = 0,
    ) -> PackedShotBatch:
        """Construct, certify, and execute one within-cycle fused-SV run."""
        if schedule is None:
            raise ValueError(
                "FusedWithinCycleSampler requires an explicit compiled schedule; "
                "circuit/dataset parsing belongs to the frontend")
        leak_kraus, leak_check = self.build_within_cycle_leak(spec)
        marshalled = self.marshal_within_cycle(
            schedule, leak_kraus, R=spec.R)
        codestate, codestate_check = self.build_codestate(schedule, spec.m)
        return self.execute_marshaled(
            spec,
            schedule=schedule,
            marshalled=marshalled,
            codestate=codestate,
            codestate_check=codestate_check,
            leak_check=leak_check,
            materialize=materialize,
            urandom=urandom,
            urandom_stride=urandom_stride,
        )

    def execute_marshaled(
        self,
        spec: RunSpec,
        *,
        schedule: Any,
        marshalled: WithinCycleMarshalled,
        codestate: torch.Tensor,
        codestate_check: dict[str, Any] | None = None,
        leak_check: dict[str, Any] | None = None,
        materialize: bool = True,
        urandom: torch.Tensor | None = None,
        urandom_stride: int = 0,
    ) -> PackedShotBatch:
        """Execute already-certified c128 inputs through the purpose-bound kernel.

        This lower seam is public so deterministic harnesses can freeze the c128
        construction once and replay the identical branch in c64.  It deliberately
        rejects pre-cast inputs: the only c64 transition is the visible cast below.
        """
        if int(marshalled.n_data) != self._N_DATA:
            raise ValueError(
                "the fused sv_traj_d3_wc kernel is specialized to 9 data qutrits "
                f"(got {marshalled.n_data})")
        if (
            codestate.dtype != torch.complex128
            or codestate.ndim != 1
            or codestate.numel() != self._STATE_DIM
        ):
            raise ValueError(
                "certified base codestate must be complex128 with shape "
                f"[{self._STATE_DIM}] (got dtype={codestate.dtype}, "
                f"shape={tuple(codestate.shape)})")
        for name in ("leak_kraus", "gate_unitaries"):
            tensor = getattr(marshalled, name)
            if tensor.dtype != torch.complex128:
                raise ValueError(
                    f"certified base {name} must be complex128 before the "
                    f"purpose-bound execution cast (got {tensor.dtype})")

        execution = cast_within_cycle_precision(marshalled, spec.dtype)
        complex_dtype = _torch_complex_dtype(spec.dtype)
        real_dtype = (
            torch.float32 if complex_dtype == torch.complex64 else torch.float64)
        codestate_execution = codestate.to(dtype=complex_dtype).contiguous()
        urandom_execution = urandom
        if urandom is not None:
            if not isinstance(urandom, torch.Tensor):
                raise TypeError("urandom must be a torch.Tensor or None")
            if urandom.device != codestate.device:
                raise ValueError(
                    "urandom must already be on the codestate device before the "
                    f"precision cast (got {urandom.device} vs {codestate.device})")
            urandom_execution = urandom.to(dtype=real_dtype).contiguous()

        header = self.build_header(spec, execution, schedule)
        header.update({
            "backend": "fused_sv_mc_within_cycle",
            "compiled_semantics": "within_cycle_qutrit_sv_mc_v1",
            "kernel_entrypoint": "sv_traj_d3_wc",
            "physics_construction_dtype": "c128",
        })
        if codestate_check is not None:
            header["codestate_check"] = dict(codestate_check)
        if leak_check is not None:
            header["within_cycle_leak_check"] = dict(leak_check)
        if spec.run_purpose in {"final", "certification"}:
            require_c128_evidence_header(header)

        from .kernels.sv_traj_d3_loader import sv_traj_d3_wc

        packed_tensor, norm_drift_tensor = sv_traj_d3_wc(
            codestate=codestate_execution,
            R=int(execution.R),
            round_op_ptr=execution.round_op_ptr,
            op_kind=execution.op_kind,
            op_uid=execution.op_uid,
            op_site=execution.op_site,
            gate_unitaries=execution.gate_unitaries,
            stab_supp_len=execution.stab_supp_len,
            stab_supp=execution.stab_supp,
            stab_supp_isx=execution.stab_supp_isx,
            leak_kraus=execution.leak_kraus,
            log_supp=execution.log_supp,
            log_supp_isx=execution.log_supp_isx,
            arm=SV_ARM_CODE[str(spec.arm).upper()],
            b=float(spec.b),
            readout_conv=SV_READOUT_CODE[str(spec.readout_conv)],
            logical_m=int(spec.m),
            N=int(spec.N),
            base_seed=int(spec.base_seed),
            shot_id_offset=0,
            wave=int(spec.W),
            urandom=urandom_execution,
            urandom_stride=int(urandom_stride),
            dtype=str(spec.dtype),
        )
        if not isinstance(packed_tensor, torch.Tensor):
            raise TypeError("sv_traj_d3_wc packed output must be a torch.Tensor")
        if not isinstance(norm_drift_tensor, torch.Tensor):
            raise TypeError("sv_traj_d3_wc norm-drift output must be a torch.Tensor")
        packed = packed_tensor.detach().cpu().numpy()
        bits = self.syndrome_bits_per_shot(execution.n_stab, execution.R)
        expected_stride = (bits + 7) // 8 + 1
        if packed.dtype != np.uint8:
            raise TypeError(
                f"sv_traj_d3_wc packed output must be uint8 (got {packed.dtype})")
        if packed.shape != (int(spec.N), expected_stride):
            raise ValueError(
                "sv_traj_d3_wc packed output shape mismatch: "
                f"got {packed.shape}, expected {(int(spec.N), expected_stride)}")
        norm_drift = np.asarray(
            norm_drift_tensor.detach().cpu().numpy(), dtype=np.float64)
        if norm_drift.shape != (int(spec.N),):
            raise ValueError(
                "sv_traj_d3_wc norm-drift shape mismatch: "
                f"got {norm_drift.shape}, expected {(int(spec.N),)}")

        out_path = None if spec.out_path is None else Path(spec.out_path)
        header_path: Path | None = None
        if out_path is not None:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            header_path = out_path.with_suffix(out_path.suffix + ".header.json")
            out_path.write_bytes(np.ascontiguousarray(packed).tobytes())
            header_path.write_text(
                json.dumps(header, indent=2, sort_keys=True), encoding="utf-8")
        diag = {
            "mean_norm_drift": (
                float(np.mean(norm_drift)) if norm_drift.size else 0.0),
            "max_norm_drift": (
                float(np.max(norm_drift)) if norm_drift.size else 0.0),
        }
        return PackedShotBatch(
            header=header,
            path=out_path,
            header_path=header_path,
            n_shots=int(spec.N),
            syndrome_bits_per_shot=bits,
            diag=diag,
            shots=packed if materialize else None,
            provenance={
                "backend": "fused_sv_mc_within_cycle",
                "compiled_semantics": "within_cycle_qutrit_sv_mc_v1",
                "run_purpose": str(spec.run_purpose),
                "precision_policy": PRECISION_POLICY,
                "evidence_eligibility": str(spec.evidence_eligibility),
            },
        )


@lru_cache(maxsize=1)
def package_build_identity() -> dict[str, Any]:
    """Return a code identity that works in editable and installed-wheel layouts.

    Git is useful provenance when a checkout exists, but it is not an installation
    contract.  The deterministic package-tree digest therefore remains mandatory
    after the wheel has left its source repository.
    """
    try:
        package_version = metadata.version("error-coupling-simulator")
    except metadata.PackageNotFoundError:
        package_version = "0+uninstalled"
    return {
        "schema": _PACKAGE_BUILD_IDENTITY_SCHEMA,
        "distribution": "error-coupling-simulator",
        "version": package_version,
        "package_tree_sha256": _package_tree_sha256(),
        "git_commit": _git_commit() or None,
    }


@lru_cache(maxsize=1)
def _package_tree_sha256() -> str:
    package_root = Path(__file__).resolve().parents[1]
    included_suffixes = {".py", ".cpp", ".cu", ".md", ".json", ".npz"}
    paths = sorted(
        path
        for path in package_root.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix in included_suffixes
    )
    digest = hashlib.sha256()
    for path in paths:
        relative = path.relative_to(package_root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        data = path.read_bytes()
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def _git_commit() -> str:
    try:
        root = Path(__file__).resolve().parents[3]
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""
