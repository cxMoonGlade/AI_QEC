from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

import numpy as np
import yaml

from scope_static.primitives.cptp_guardrail import build_cptp_guardrail_audit
from .full_circuit_cudaq import (
    _build_full_circuit_oracle_mechanisms,
    _operation_sites_from_mechanisms,
    build_full_circuit_mechanism_definition_audit,
    generate_full_circuit_cudaq_teacher_dataset,
)
from scope_static.protocols import DATA_PREPARATION_STAGE
from .contract import FULL_CIRCUIT_TEACHER_MODEL
from scope_static.primitives.probe_catalog import _merged_config
from .physicality_audit import run_teacher_physicality_audit


STAGE_NAME = "Layer1.P_teacher"
DEFAULT_OUTPUT_DIR = "outputs/scope_static/Layer1P_teacher"
DEFAULT_AUDIT_SUBDIR = "Layer1_teacher_physicality_audit"
DEFAULT_TOLERANCE_MODE = "strict"
DEFAULT_PROBABILITY_TOLERANCE = 1.0e-12
DEFAULT_RANDOM_STATE_COUNT = 4
PRE_SAMPLING_TOLERANCE = 1.0e-9


def generate_layer1p_teacher_dataset(
    config: Mapping[str, object] | None = None,
    *,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    audit_output_dir: str | Path | None = None,
    tolerance_mode: str = DEFAULT_TOLERANCE_MODE,
    probability_tolerance: float = DEFAULT_PROBABILITY_TOLERANCE,
    random_state_count: int = DEFAULT_RANDOM_STATE_COUNT,
    enforce_pre_sampling_contract: bool = True,
    enforce_post_sampling_physicality: bool = True,
) -> dict[str, object]:
    """Generate a Layer1.P teacher with a blocking physical-process contract.

    Layer1.P is a teacher, not just an audit: it validates the declared local
    CPTP/POVM mechanism modules before sampling, samples full-circuit CUDA-Q
    observations, and then blocks the artifact if the generated observations
    fail the Layer1.P physicality audit.
    """

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    cfg = layer1p_teacher_config(config)
    pre_sampling = build_layer1p_pre_sampling_contract(cfg)
    (output / "layer1p_pre_sampling_contract.json").write_text(json.dumps(_json_safe(pre_sampling), indent=2, sort_keys=True) + "\n")
    if enforce_pre_sampling_contract and not bool(pre_sampling.get("passed", False)):
        raise ValueError("Layer1.P pre-sampling physical-process contract failed")

    full_summary = generate_full_circuit_cudaq_teacher_dataset(cfg, output_dir=output)
    full_summary_path = output / "summary.json"
    if full_summary_path.exists():
        (output / "full_circuit_cudaq_summary.json").write_text(full_summary_path.read_text())

    audit_output = Path(audit_output_dir) if audit_output_dir is not None else output / DEFAULT_AUDIT_SUBDIR
    physicality = run_teacher_physicality_audit(
        teacher_dir=output,
        output_dir=audit_output,
        tolerance_mode=str(tolerance_mode),
        probability_tolerance=float(probability_tolerance),
        random_state_count=int(random_state_count),
    )
    contract = layer1p_teacher_contract(
        cfg=cfg,
        output=output,
        audit_output=audit_output,
        pre_sampling_contract=pre_sampling,
        full_circuit_summary=full_summary,
        physicality_audit=physicality,
        enforce_pre_sampling_contract=bool(enforce_pre_sampling_contract),
        enforce_post_sampling_physicality=bool(enforce_post_sampling_physicality),
    )
    acceptance = layer1p_acceptance_audit(contract)
    result = {
        "schema": "scope_static_layer1p_teacher_v1",
        "stage": STAGE_NAME,
        "public_layer": DATA_PREPARATION_STAGE.metadata(artifact_stage=STAGE_NAME, substage="physical_process_teacher"),
        "teacher_model": "layer1p_full_circuit_cudaq",
        "physical_teacher_model": "layer1p_full_circuit_cudaq",
        "output_dir": str(output),
        "audit_output_dir": str(audit_output),
        "num_probes": full_summary.get("num_probes"),
        "num_qubits": full_summary.get("num_qubits"),
        "num_physical_qubits": full_summary.get("num_physical_qubits"),
        "num_observation_slots": full_summary.get("num_observation_slots"),
        "circuit_depth": full_summary.get("circuit_depth"),
        "configured_circuit_depth": full_summary.get("configured_circuit_depth"),
        "effective_circuit_depth": full_summary.get("effective_circuit_depth"),
        "circuit_depth_semantics": full_summary.get("circuit_depth_semantics"),
        "shots": full_summary.get("shots"),
        "mechanism_counts": full_summary.get("mechanism_counts", {}),
        "balanced_min_instances_per_mechanism": full_summary.get("balanced_min_instances_per_mechanism"),
        "num_circuit_batches": full_summary.get("num_circuit_batches"),
        "sampling": full_summary.get("sampling"),
        "sampling_audit": full_summary.get("sampling_audit"),
        "active_probe_manifest": full_summary.get("active_probe_manifest"),
        "noise_application_audit": full_summary.get("noise_application_audit"),
        "non_clifford_audit": full_summary.get("non_clifford_audit"),
        "claim_boundary": {
            "is_teacher_generator_not_posthoc_only_audit": True,
            "pre_sampling_cptp_povm_contract_enforced": bool(enforce_pre_sampling_contract),
            "post_sampling_physicality_audit_enforced": bool(enforce_post_sampling_physicality),
            "samples_observations_from_cptp_or_instrument_defined_processes": True,
            "data_are_cptp": False,
            "uses_full_circuit_cudaq_born_rule_sampling": True,
            "does_not_claim_hardware_ground_truth": True,
            "does_not_claim_arbitrary_cptp_gksl_learning": True,
            "leakage_is_computational_subspace_surrogate_unless_qutrit_model_declared": True,
        },
        "config": {
            **_json_safe(cfg),
            "audit_output_dir": str(audit_output),
            "tolerance_mode": str(tolerance_mode),
            "probability_tolerance": float(probability_tolerance),
            "random_state_count": int(random_state_count),
            "enforce_pre_sampling_contract": bool(enforce_pre_sampling_contract),
            "enforce_post_sampling_physicality": bool(enforce_post_sampling_physicality),
        },
        "pre_sampling_contract": pre_sampling,
        "full_circuit_cudaq_summary": full_summary,
        "teacher_physicality_audit": physicality,
        "layer1p_teacher_contract": contract,
        "acceptance_audit": acceptance,
        "decision": "layer1p_teacher_generated" if bool(acceptance.get("passed", False)) else "layer1p_teacher_failed",
    }
    _write_outputs(output, result)
    if enforce_post_sampling_physicality and not bool(acceptance.get("passed", False)):
        raise RuntimeError("Layer1.P generated teacher failed physicality acceptance")
    return result


def layer1p_teacher_config(config: Mapping[str, object] | None = None) -> dict[str, object]:
    cfg = _merged_config(dict(config or {}))
    cfg["backend"] = "cudaq"
    cfg["physical_teacher_model"] = FULL_CIRCUIT_TEACHER_MODEL
    cfg["layer1p_teacher_contract_required"] = True
    cfg["layer1p_teacher_model"] = "layer1p_full_circuit_cudaq"
    cfg.setdefault("full_circuit_cudaq_noise_mode", "hybrid")
    return cfg


def build_layer1p_pre_sampling_contract(config: Mapping[str, object] | None = None) -> dict[str, object]:
    cfg = layer1p_teacher_config(config)
    mechanisms, repetitions, sampling_contract = _build_full_circuit_oracle_mechanisms(cfg)
    groups: dict[int, list[object]] = {}
    for spec in mechanisms:
        groups.setdefault(int(spec.circuit_id), []).append(spec)
    operation_sites_by_group = {
        int(circuit_id): _operation_sites_from_mechanisms(specs)  # type: ignore[arg-type]
        for circuit_id, specs in groups.items()
    }
    cptp_guardrail = build_cptp_guardrail_audit(mechanisms, tolerance=PRE_SAMPLING_TOLERANCE)
    definition = build_full_circuit_mechanism_definition_audit(
        mechanisms,
        operation_sites_by_group=operation_sites_by_group,
    )
    checks = {
        "full_circuit_cudaq_teacher_model": str(cfg.get("physical_teacher_model")) == FULL_CIRCUIT_TEACHER_MODEL,
        "local_cptp_or_valid_readout_modules": bool(cptp_guardrail.get("passed", False)),
        "mechanism_definition_contract_passed": bool(definition.get("passed", False)),
        "mechanism_instances_declared": bool(len(mechanisms) > 0),
        "circuit_batches_declared": bool(int(repetitions) > 0),
        "sampling_contract_declared": str(sampling_contract) in {"balanced", "weighted"},
        "uses_born_rule_full_circuit_sampler": True,
        "no_posthoc_only_teacher_claim": True,
    }
    return {
        "schema": "scope_static_layer1p_pre_sampling_contract_v1",
        "passed": bool(all(checks.values())),
        "checks": checks,
        "contract_statement": "Layer1.P composes ideal circuit operations with declared local CPTP channels, valid stochastic readout maps embedded as POVMs, or declared computational-subspace surrogates, then samples the resulting observation distribution with CUDA-Q/Born-rule sampling.",
        "observation_distribution": "p_Theta(y | c) = Tr[M_y C_Theta(c)(rho_0)]",
        "mechanism_record_count": int(len(mechanisms)),
        "active_mechanism_count": int(len({spec.mechanism_id for spec in mechanisms})),
        "circuit_batch_count": int(repetitions),
        "sampling_contract": str(sampling_contract),
        "cptp_guardrail_audit": cptp_guardrail,
        "mechanism_definition_audit": definition,
    }


def layer1p_teacher_contract(
    *,
    cfg: Mapping[str, object],
    output: Path,
    audit_output: Path,
    pre_sampling_contract: Mapping[str, object],
    full_circuit_summary: Mapping[str, object],
    physicality_audit: Mapping[str, object],
    enforce_pre_sampling_contract: bool,
    enforce_post_sampling_physicality: bool,
) -> dict[str, object]:
    physicality_summary = dict(physicality_audit.get("summary", {})) if isinstance(physicality_audit.get("summary", {}), dict) else {}
    return {
        "schema": "scope_static_layer1p_teacher_contract_v1",
        "teacher_stage": STAGE_NAME,
        "teacher_model": "layer1p_full_circuit_cudaq",
        "underlying_sampler": FULL_CIRCUIT_TEACHER_MODEL,
        "output_dir": str(output),
        "audit_output_dir": str(audit_output),
        "pre_sampling_contract_path": str(output / "layer1p_pre_sampling_contract.json"),
        "post_sampling_physicality_audit_path": str(audit_output / "metrics.json"),
        "full_circuit_cudaq_summary_path": str(output / "full_circuit_cudaq_summary.json"),
        "pre_sampling_contract_enforced": bool(enforce_pre_sampling_contract),
        "post_sampling_physicality_audit_enforced": bool(enforce_post_sampling_physicality),
        "pre_sampling_contract_passed": bool(pre_sampling_contract.get("passed", False)),
        "post_sampling_physicality_passed": bool(physicality_summary.get("teacher_physicality_passed", False)),
        "sampling_completed": bool(dict(full_circuit_summary.get("sampling", {})).get("completed_probe_circuits", 0) == full_circuit_summary.get("num_probes")),
        "num_mechanisms": int(physicality_summary.get("total_mechanisms", 0)),
        "num_channel_instances_checked": int(physicality_summary.get("total_channel_instances_checked", 0)),
        "num_contexts_checked": int(physicality_summary.get("total_contexts_checked", 0)),
        "total_failures": int(physicality_summary.get("total_failures", 0)),
        "silent_renormalization_used": bool(physicality_summary.get("silent_renormalization_used", False)),
        "physical_process_claim": "teacher_samples_observations_from_cptp_povm_or_valid_declared_surrogate_processes",
        "data_are_cptp": False,
        "config_sha256": _stable_json_digest(cfg),
    }


def layer1p_acceptance_audit(contract: Mapping[str, object]) -> dict[str, object]:
    checks = {
        "is_first_class_teacher_generator": str(contract.get("teacher_stage")) == STAGE_NAME,
        "pre_sampling_contract_enforced": bool(contract.get("pre_sampling_contract_enforced", False)),
        "post_sampling_physicality_audit_enforced": bool(contract.get("post_sampling_physicality_audit_enforced", False)),
        "pre_sampling_contract_passed": bool(contract.get("pre_sampling_contract_passed", False)),
        "sampling_completed": bool(contract.get("sampling_completed", False)),
        "post_sampling_physicality_passed": bool(contract.get("post_sampling_physicality_passed", False)),
        "mechanism_failures_zero": int(contract.get("total_failures", 1)) == 0,
        "silent_renormalization_not_used": not bool(contract.get("silent_renormalization_used", True)),
        "does_not_claim_data_are_cptp": not bool(contract.get("data_are_cptp", True)),
    }
    return {
        "schema": "scope_static_layer1p_teacher_acceptance_v1",
        "passed": bool(all(checks.values())),
        "checks": checks,
    }


def _write_outputs(output: Path, result: Mapping[str, object]) -> None:
    artifacts = {
        "summary.json": result,
        "layer1p_teacher_contract.json": result["layer1p_teacher_contract"],
        "acceptance_audit.json": result["acceptance_audit"],
        "layer1p_pre_sampling_contract.json": result["pre_sampling_contract"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(_json_safe(payload), indent=2, sort_keys=True) + "\n")
    (output / "config.yaml").write_text(yaml.safe_dump({"layer1p_teacher": result["config"]}, sort_keys=False))
    (output / "summary.md").write_text(format_layer1p_teacher_summary(result))


def format_layer1p_teacher_summary(result: Mapping[str, object]) -> str:
    acceptance = dict(result.get("acceptance_audit", {})) if isinstance(result.get("acceptance_audit", {}), dict) else {}
    contract = dict(result.get("layer1p_teacher_contract", {})) if isinstance(result.get("layer1p_teacher_contract", {}), dict) else {}
    return "\n".join(
        [
            "# Layer1.P Teacher",
            "",
            f"- Decision: `{result.get('decision')}`",
            f"- Acceptance passed: `{str(bool(acceptance.get('passed', False))).lower()}`",
            f"- Mechanisms: `{contract.get('num_mechanisms')}`",
            f"- Channel instances checked: `{contract.get('num_channel_instances_checked')}`",
            f"- Contexts checked: `{contract.get('num_contexts_checked')}`",
            f"- Total failures: `{contract.get('total_failures')}`",
            f"- Pre-sampling contract enforced: `{str(bool(contract.get('pre_sampling_contract_enforced', False))).lower()}`",
            f"- Post-sampling physicality enforced: `{str(bool(contract.get('post_sampling_physicality_audit_enforced', False))).lower()}`",
            "",
            "## Claim Boundary",
            "",
            "Layer1.P is a teacher generator: it validates the declared local CPTP/POVM mechanism process before sampling, samples full-circuit CUDA-Q observations, and blocks the artifact when the post-sampling physicality audit fails. It does not claim that data are CPTP.",
            "",
        ]
    )


def _stable_json_digest(payload: Mapping[str, object]) -> str:
    import hashlib

    text = json.dumps(_json_safe(dict(payload)), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _json_safe(value):
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    return value
