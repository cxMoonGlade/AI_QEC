from __future__ import annotations

import json
from pathlib import Path
import re
import time

import numpy as np

from scope_static.primitives.born_local import (
    BORN_LOCAL_DEPTH_SEMANTICS,
    BORN_LOCAL_EFFECTIVE_CIRCUIT_DEPTH,
    BORN_LOCAL_SUPPORTED_MECHANISMS,
    BORN_LOCAL_UNSUPPORTED_MECHANISM_REASONS,
    born_local_probability_tables,
    outcome_zz_correlation,
)
from scope_static.primitives.cptp_guardrail import build_cptp_guardrail_audit_from_records
from scope_static.protocols import DATA_PREPARATION_STAGE
from scope_static.primitives.mechanism_catalog import READOUT_MECHANISM_IDS, RZZ_FAMILY_IDS
from .contract import LOCAL_OBSERVABLE_TEACHER_MODEL, PHYC1_LEGACY_STAGE_NAME, probe_names as phyc1_probe_names
from scope_static.primitives.ptm import channel_fingerprint, probe_response_fingerprint, rzz_type_feature_vector
from scope_static.primitives.probe_catalog import _build_balanced_oracle_mechanisms, _merged_config, build_probe_basis_manifest

READOUT_ALIAS_GROUP = tuple(sorted(READOUT_MECHANISM_IDS, key=lambda value: int(value[1:])))
RZZ_ALIAS_GROUP = tuple(RZZ_FAMILY_IDS[:4])
SELF_DISTINGUISHABILITY_ALIAS_GROUPS = {
    "readout_bias_context": READOUT_ALIAS_GROUP,
    "readout_symmetric_vs_context": ("M3", "M16"),
    "rzz_gate_family": RZZ_ALIAS_GROUP,
    "rare_low_margin_last_run": ("M5", "M9", "M10", "M12", "M17", "M18", "M19"),
}


def generate_local_observable_teacher_dataset(
    config: dict[str, object] | None = None,
    *,
    output_dir: str | Path,
) -> dict[str, object]:
    """Generate PHYS1-compatible sampled observations with a GPU local-response teacher.

    This teacher is not a global circuit simulator. It samples learner-visible
    local probe responses for each mechanism location directly on Torch CUDA,
    preserving the PHYS1 artifact contract while avoiding global bitstring
    simulation.
    """

    cfg = _merged_config(config)
    cfg["multicircuit_teacher_batch"] = True
    cfg.setdefault("probe_set", "rzz_local_tomography")
    cfg.setdefault("local_observable_response_model", "separability_v2")
    response_model = _normalize_response_model(str(cfg.get("local_observable_response_model", "separability_v2")))
    cfg["local_observable_response_model"] = response_model
    configured_circuit_depth = int(cfg.get("circuit_depth", 1))
    effective_circuit_depth = _effective_circuit_depth(response_model, configured_circuit_depth)
    cfg["configured_circuit_depth"] = int(configured_circuit_depth)
    cfg["effective_circuit_depth"] = int(effective_circuit_depth)
    cfg["circuit_depth_semantics"] = _circuit_depth_semantics(response_model)
    records, repetitions, sampling_contract = _build_local_observable_records(cfg)
    born_scope = _born_local_scope_audit(records)
    if response_model == "born_local":
        records = _filter_born_local_supported_records(records)
        if not records:
            raise ValueError("Born-local teacher scope removed every mechanism record")
        cfg["born_local_scope"] = born_scope
    physical_num_qubits = int(cfg.get("num_qubits", 30))
    slot_remap_enabled = bool(cfg.get("local_observable_slot_remap", True))
    cfg["local_observable_slot_remap"] = slot_remap_enabled
    observation_slots = (
        max(physical_num_qubits, _max_observation_slots_required(records))
        if slot_remap_enabled
        else physical_num_qubits
    )
    cfg["num_physical_qubits"] = int(physical_num_qubits)
    cfg["num_observation_slots"] = int(observation_slots)
    slot_audit = (
        _assign_nonoverlapping_observation_slots(records, num_qubits=observation_slots, physical_num_qubits=physical_num_qubits)
        if slot_remap_enabled
        else _disabled_observation_slot_audit(records, num_qubits=observation_slots, physical_num_qubits=physical_num_qubits)
    )
    base_probe_names = phyc1_probe_names(str(cfg.get("probe_set", "rzz_local_tomography")))
    probe_names = [f"c{circuit_id}:{name}" for circuit_id in range(repetitions) for name in base_probe_names]
    shots = int(cfg.get("shots", 10_000))
    seed = int(cfg.get("seed", 0))

    started = time.perf_counter()
    observations, sampling_audit = _sample_local_observations(
        records,
        probe_names,
        shots=shots,
        num_qubits=observation_slots,
        seed=seed,
        response_model=response_model,
        theta=float(cfg.get("theta", 0.18)),
        configured_circuit_depth=configured_circuit_depth,
    )
    total_seconds = time.perf_counter() - started
    sampling_audit["total_wall_clock_seconds"] = float(total_seconds)
    sampling_audit["observation_slot_remap"] = slot_audit
    self_preflight = build_self_distinguishability_preflight(
        records,
        probe_names,
        response_model=response_model,
        num_qubits=observation_slots,
        theta=float(cfg.get("theta", 0.18)),
        configured_circuit_depth=configured_circuit_depth,
    )

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    np.savez(
        output / "observations.npz",
        observations=observations,
        probe_names=np.asarray(probe_names),
        shots=np.asarray([shots], dtype=np.int64),
    )
    (output / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2, sort_keys=True) + "\n")
    (output / "teacher_config.json").write_text(json.dumps(_json_safe(cfg), indent=2, sort_keys=True) + "\n")
    (output / "sampling_audit.json").write_text(json.dumps(sampling_audit, indent=2, sort_keys=True) + "\n")
    (output / "self_distinguishability_preflight.json").write_text(json.dumps(_json_safe(self_preflight), indent=2, sort_keys=True) + "\n")
    cptp_guardrail = build_cptp_guardrail_audit_from_records(records)
    (output / "cptp_guardrail_audit.json").write_text(json.dumps(_json_safe(cptp_guardrail), indent=2, sort_keys=True) + "\n")
    probe_manifest = build_probe_basis_manifest(probe_names, num_qubits=observation_slots, circuit_depth=effective_circuit_depth)
    probe_manifest["num_physical_qubits"] = int(physical_num_qubits)
    probe_manifest["num_observation_slots"] = int(observation_slots)
    probe_manifest["configured_circuit_depth"] = int(configured_circuit_depth)
    probe_manifest["effective_circuit_depth"] = int(effective_circuit_depth)
    probe_manifest["circuit_depth_semantics"] = _circuit_depth_semantics(response_model)
    (output / "active_probe_manifest.json").write_text(json.dumps(probe_manifest, indent=2, sort_keys=True) + "\n")
    summary = {
        "schema": "scope_static_local_observable_gpu_teacher_v1",
        "stage": PHYC1_LEGACY_STAGE_NAME,
        "public_layer": DATA_PREPARATION_STAGE.metadata(artifact_stage=PHYC1_LEGACY_STAGE_NAME, substage="local_observable_teacher"),
        "teacher_model": LOCAL_OBSERVABLE_TEACHER_MODEL,
        "local_observable_response_model": response_model,
        "born_local_scope": born_scope if response_model == "born_local" else None,
        "output_dir": str(output),
        "num_qubits": int(observation_slots),
        "num_physical_qubits": int(physical_num_qubits),
        "num_observation_slots": int(observation_slots),
        "configured_circuit_depth": int(configured_circuit_depth),
        "effective_circuit_depth": int(effective_circuit_depth),
        "circuit_depth_semantics": _circuit_depth_semantics(response_model),
        "num_probes": int(len(probe_names)),
        "shots": int(shots),
        "mechanism_counts": _counts(str(record["oracle_label"]) for record in records),
        "sampling_contract": sampling_contract,
        "balanced_min_instances_per_mechanism": int(repetitions),
        "multicircuit_teacher_batch": True,
        "num_circuit_batches": int(repetitions),
        "sampling": sampling_audit,
        "cptp_guardrail_passed": bool(cptp_guardrail["passed"]),
        "cptp_guardrail_audit": str(output / "cptp_guardrail_audit.json"),
        "observation_slot_remap": slot_audit,
        "self_distinguishability_preflight": str(output / "self_distinguishability_preflight.json"),
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(_summary_markdown(summary))
    return summary


def _build_local_observable_records(cfg: dict[str, object]) -> tuple[list[dict[str, object]], int, str]:
    default_count = max(2, int(cfg.get("balanced_min_instances_per_mechanism", 3)))
    instance_counts = _mechanism_instance_counts(cfg, default_count=default_count)
    if instance_counts:
        repetitions = max(default_count, max(instance_counts.values()))
        sampling_contract = "weighted"
    else:
        repetitions = default_count
        sampling_contract = "balanced"
    cfg["balanced_min_instances_per_mechanism"] = int(repetitions)
    seen: dict[str, int] = {}
    records = []
    mechanisms = _build_balanced_oracle_mechanisms(cfg)
    for spec in mechanisms:
        count = seen.get(spec.mechanism_id, 0)
        target_count = instance_counts.get(spec.mechanism_id, default_count) if instance_counts else repetitions
        if count >= int(target_count):
            continue
        seen[spec.mechanism_id] = count + 1
        records.append(
            {
                "location_id": len(records),
                **spec.audit_dict(),
                "oracle_label": spec.mechanism_id,
                "oracle_label_evaluator_only": True,
            }
        )
    return records, int(repetitions), sampling_contract


def _assign_nonoverlapping_observation_slots(
    records: list[dict[str, object]],
    *,
    num_qubits: int,
    physical_num_qubits: int | None = None,
) -> dict[str, object]:
    """Give each local mechanism in a circuit its own sampled-observation slots.

    Full-circuit samplers naturally combine all mechanisms into one bit tensor.
    The local-observable teacher instead emits per-mechanism local responses; if
    two records share the same probe/qubit cell, the later response overwrites
    the earlier one.  A 30-qubit allM circuit needs 24 local slots, so we can
    preserve the PHYS1 tensor shape while avoiding destructive overlap.
    """

    by_circuit: dict[int, list[dict[str, object]]] = {}
    for record in records:
        by_circuit.setdefault(int(record.get("circuit_id", 0)), []).append(record)
    remapped = 0
    skipped: list[int] = []
    max_slots = 0
    for circuit_id, local_records in by_circuit.items():
        ordered = sorted(local_records, key=lambda record: _mechanism_sort_key(str(record.get("oracle_label", ""))))
        required = sum(2 if int(record.get("num_qubits", len(record.get("qubits", [])))) >= 2 else 1 for record in ordered)
        max_slots = max(max_slots, int(required))
        if required > int(num_qubits):
            skipped.append(int(circuit_id))
            continue
        cursor = 0
        offset = (7 * int(circuit_id)) % max(1, int(num_qubits))
        for record in ordered:
            width = 2 if int(record.get("num_qubits", len(record.get("qubits", [])))) >= 2 else 1
            original = [int(value) for value in record.get("qubits", [])]
            slots = [int((offset + cursor + idx) % int(num_qubits)) for idx in range(width)]
            record["physical_qubits"] = original
            record["qubits"] = slots
            record["local_observable_slot_remap"] = True
            cursor += width
            remapped += 1
    return {
        "schema": "scope_static_local_observable_slot_remap_v1",
        "enabled": bool(remapped),
        "reason": "avoid per-record sampled-observation overwrite in the local-observable teacher",
        "num_records_remapped": int(remapped),
        "num_circuits": int(len(by_circuit)),
        "max_slots_required_per_circuit": int(max_slots),
        "num_qubits": int(num_qubits),
        "num_physical_qubits": int(physical_num_qubits if physical_num_qubits is not None else num_qubits),
        "num_observation_slots": int(num_qubits),
        "skipped_circuit_ids": skipped,
    }


def _disabled_observation_slot_audit(records: list[dict[str, object]], *, num_qubits: int, physical_num_qubits: int | None = None) -> dict[str, object]:
    by_circuit = {int(record.get("circuit_id", 0)) for record in records}
    return {
        "schema": "scope_static_local_observable_slot_remap_v1",
        "enabled": False,
        "reason": "disabled for PHYC2.no_slot_remap_ablation; local responses may overwrite shared probe/qubit cells",
        "num_records_remapped": 0,
        "num_circuits": int(len(by_circuit)),
        "max_slots_required_per_circuit": 0,
        "num_qubits": int(num_qubits),
        "num_physical_qubits": int(physical_num_qubits if physical_num_qubits is not None else num_qubits),
        "num_observation_slots": int(num_qubits),
        "skipped_circuit_ids": [],
    }


def _max_observation_slots_required(records: list[dict[str, object]]) -> int:
    by_circuit: dict[int, int] = {}
    for record in records:
        width = 2 if int(record.get("num_qubits", len(record.get("qubits", [])))) >= 2 else 1
        circuit_id = int(record.get("circuit_id", 0))
        by_circuit[circuit_id] = by_circuit.get(circuit_id, 0) + int(width)
    return max(by_circuit.values()) if by_circuit else 1


def _sample_local_observations(
    records: list[dict[str, object]],
    probe_names: list[str],
    *,
    shots: int,
    num_qubits: int,
    seed: int,
    response_model: str = "separability_v2",
    theta: float = 0.18,
    configured_circuit_depth: int = 1,
) -> tuple[np.ndarray, dict[str, object]]:
    import torch

    model = _normalize_response_model(response_model)
    if not torch.cuda.is_available():
        raise RuntimeError("local_observable_gpu teacher requires torch.cuda.is_available()")
    device = torch.device("cuda")
    started = time.perf_counter()
    probabilities = torch.full((len(probe_names), int(num_qubits)), 0.5, dtype=torch.float32, device=device)
    cpu_probability_table = np.full((len(probe_names), int(num_qubits)), 0.5, dtype=np.float32)
    joint_sampling_entries: list[dict[str, object]] = []
    for record in records:
        qubits = [int(value) for value in record.get("qubits", [])]
        probe_indices = [int(value) for value in record.get("probe_indices", [])]
        if not qubits or not probe_indices:
            continue
        local_probe_names = [probe_names[probe_idx] for probe_idx in probe_indices if 0 <= probe_idx < len(probe_names)]
        local = _record_probability_table(record, local_probe_names, response_model=model, num_qubits=num_qubits, theta=float(theta))
        for local_idx, probe_idx in enumerate(probe_indices):
            if probe_idx < 0 or probe_idx >= len(probe_names):
                continue
            for pos, qubit in enumerate(qubits):
                if 0 <= qubit < int(num_qubits):
                    p = float(local[local_idx % local.shape[0], pos % local.shape[1]])
                    cpu_probability_table[probe_idx, qubit] = p
        if model == "born_local" and len(qubits) >= 2:
            outcome_table, _ = _record_born_local_tables(record, local_probe_names, num_qubits=num_qubits, theta=float(theta))
            valid_probe_indices = [probe_idx for probe_idx in probe_indices if 0 <= probe_idx < len(probe_names)]
            if len(valid_probe_indices) == outcome_table.shape[0]:
                joint_sampling_entries.append(
                    {
                        "probe_indices": valid_probe_indices,
                        "left": int(qubits[0]),
                        "right": int(qubits[1]),
                        "outcomes": outcome_table.astype(np.float32),
                    }
                )
    probabilities.copy_(torch.as_tensor(cpu_probability_table, dtype=torch.float32, device=device))
    torch.cuda.synchronize()
    probability_seconds = time.perf_counter() - started

    gen = torch.Generator(device=device)
    gen.manual_seed(int(seed))
    sample_started = time.perf_counter()
    random = torch.rand((len(probe_names), int(shots), int(num_qubits)), dtype=torch.float32, device=device, generator=gen)
    observations_gpu = random < probabilities[:, None, :]
    del random
    if model == "born_local":
        overlay_audit = {"enabled": False, "reason": "born_local samples exact local joint POVMs directly", "num_overlay_entries": 0, "num_records": 0}
        joint_sampling_audit = _sample_born_local_joint_entries(
            observations_gpu,
            joint_sampling_entries,
            shots=int(shots),
            generator=gen,
        )
    else:
        overlay_audit = _apply_pair_correlation_overlays(
            observations_gpu,
            records,
            probe_names,
            generator=gen,
            response_model=model,
        )
        joint_sampling_audit = {"enabled": False, "num_entries": 0, "num_records": 0}
    torch.cuda.synchronize()
    sampling_seconds = time.perf_counter() - sample_started
    copy_started = time.perf_counter()
    observations = observations_gpu.to(dtype=torch.uint8).cpu().numpy()
    torch.cuda.synchronize()
    copy_seconds = time.perf_counter() - copy_started
    audit = {
        "schema": "scope_static_local_observable_gpu_sampling_audit_v1",
        "teacher_model": LOCAL_OBSERVABLE_TEACHER_MODEL,
        "local_observable_response_model": model,
        "backend": "torch_cuda",
        "device": str(torch.cuda.get_device_name(0)),
        "num_probes": int(len(probe_names)),
        "shots": int(shots),
        "num_qubits": int(num_qubits),
        "configured_circuit_depth": int(configured_circuit_depth),
        "effective_circuit_depth": int(_effective_circuit_depth(model, configured_circuit_depth)),
        "circuit_depth_semantics": _circuit_depth_semantics(model),
        "total_requested_bits": int(len(probe_names) * int(shots) * int(num_qubits)),
        "probability_table_wall_clock_seconds": float(probability_seconds),
        "sampling_wall_clock_seconds": float(sampling_seconds),
        "host_copy_wall_clock_seconds": float(copy_seconds),
        "pair_correlation_overlay": overlay_audit,
        "born_local_joint_sampling": joint_sampling_audit,
        "metrics_are_wall_clock": True,
        "contract_note": "Samples local mechanism responses directly; not a global full-circuit simulator.",
    }
    return observations, audit


def _record_probability_profile(
    record: dict[str, object],
    probe_names_or_count: list[str] | int,
    *,
    response_model: str = "separability_v2",
) -> np.ndarray:
    from scope_static.primitives.channels import MechanismSpec

    model = _normalize_response_model(response_model)
    spec = MechanismSpec(
        mechanism_id=str(record["oracle_label"]),
        name=str(record.get("name", record["oracle_label"])),
        num_qubits=int(record.get("num_qubits", 1)),
        parameters=dict(record.get("parameters", {})),
        instruction=None if record.get("instruction") is None else str(record.get("instruction")),
        qubits=tuple(int(value) for value in record.get("qubits", [])),
        circuit_id=int(record.get("circuit_id", 0)),
        probe_indices=tuple(int(value) for value in record.get("probe_indices", [])),
    )
    raw = np.concatenate(
        [
            channel_fingerprint(spec, paper_informed=True),
            probe_response_fingerprint(spec),
            rzz_type_feature_vector(spec),
        ]
    )
    if raw.size == 0:
        raw = np.zeros(1, dtype=np.float64)
    if isinstance(probe_names_or_count, int):
        probe_names = [f"probe_{idx}" for idx in range(max(1, int(probe_names_or_count)))]
    else:
        probe_names = [str(name) for name in probe_names_or_count]
    if model == "born_local":
        _, marginals = _record_born_local_tables(record, probe_names, num_qubits=None, theta=0.18)
        return np.mean(marginals, axis=1).astype(np.float32)
    if model == "separability_v1":
        profile = _fingerprint_response_profile(raw, probe_names)
    else:
        profile = _branch_specific_probability_profile(spec, raw, probe_names)
    return np.clip(profile, 0.02, 0.98).astype(np.float32)


def _record_probability_table(
    record: dict[str, object],
    probe_names: list[str],
    *,
    response_model: str,
    num_qubits: int,
    theta: float,
) -> np.ndarray:
    model = _normalize_response_model(response_model)
    if model == "born_local":
        _, marginals = _record_born_local_tables(record, probe_names, num_qubits=int(num_qubits), theta=float(theta))
        return marginals.astype(np.float32)
    profile = _record_probability_profile(record, probe_names, response_model=model).astype(np.float32)
    width = max(1, len(record.get("qubits", [])))
    table = np.zeros((max(1, len(probe_names)), width), dtype=np.float32)
    for local_idx in range(table.shape[0]):
        for pos in range(width):
            table[local_idx, pos] = float(profile[(local_idx + 7 * pos) % profile.size])
    return table


def _record_born_local_tables(
    record: dict[str, object],
    probe_names: list[str],
    *,
    num_qubits: int | None,
    theta: float,
) -> tuple[np.ndarray, np.ndarray]:
    from scope_static.primitives.channels import MechanismSpec

    spec = MechanismSpec(
        mechanism_id=str(record["oracle_label"]),
        name=str(record.get("name", record["oracle_label"])),
        num_qubits=int(record.get("num_qubits", 1)),
        parameters=dict(record.get("parameters", {})),
        instruction=None if record.get("instruction") is None else str(record.get("instruction")),
        qubits=tuple(int(value) for value in record.get("physical_qubits", record.get("qubits", []))),
        circuit_id=int(record.get("circuit_id", 0)),
        probe_indices=tuple(int(value) for value in record.get("probe_indices", [])),
    )
    return born_local_probability_tables(
        spec,
        probe_names,
        theta=float(theta),
        num_qubits=num_qubits,
        physical_qubits=tuple(int(value) for value in record.get("physical_qubits", record.get("qubits", []))),
    )


def _record_pair_correlation_profile(
    record: dict[str, object],
    probe_names_or_count: list[str] | int,
    *,
    response_model: str = "separability_v2",
) -> np.ndarray:
    model = _normalize_response_model(response_model)
    if model == "born_local":
        if isinstance(probe_names_or_count, int):
            probe_names = [f"probe_{idx}" for idx in range(max(1, int(probe_names_or_count)))]
        else:
            probe_names = [str(name) for name in probe_names_or_count]
        if int(record.get("num_qubits", 1)) < 2:
            return np.zeros(max(1, len(probe_names)), dtype=np.float32)
        outcome_table, _ = _record_born_local_tables(record, probe_names, num_qubits=None, theta=0.18)
        return np.asarray([outcome_zz_correlation(row) for row in outcome_table], dtype=np.float32)
    if model != "separability_v2":
        count = int(probe_names_or_count) if isinstance(probe_names_or_count, int) else len(probe_names_or_count)
        return np.zeros(max(1, count), dtype=np.float32)
    if isinstance(probe_names_or_count, int):
        probe_names = [f"probe_{idx}" for idx in range(max(1, int(probe_names_or_count)))]
    else:
        probe_names = [str(name) for name in probe_names_or_count]
    mech = str(record.get("oracle_label", record.get("mechanism_id", "")))
    if mech not in RZZ_ALIAS_GROUP:
        return np.zeros(max(1, len(probe_names)), dtype=np.float32)
    values = []
    for name in probe_names:
        tokens = _probe_tokens(name)
        mx = 0.5 * (_axis_indicator(tokens["meas_left"], "X") + _axis_indicator(tokens["meas_right"], "X"))
        my = 0.5 * (_axis_indicator(tokens["meas_left"], "Y") + _axis_indicator(tokens["meas_right"], "Y"))
        mz = 0.5 * (_axis_indicator(tokens["meas_left"], "Z") + _axis_indicator(tokens["meas_right"], "Z"))
        mixed_xy = 1.0 if {tokens["meas_left"], tokens["meas_right"]} == {"X", "Y"} else 0.0
        same_xy = 1.0 if tokens["meas_left"] == tokens["meas_right"] and tokens["meas_left"] in {"X", "Y"} else 0.0
        parity = _parity_sign(tokens["parity"])
        prep_product = _prep_sign(tokens["prep_left"]) * _prep_sign(tokens["prep_right"])
        if mech == "M8":
            score = 1.8 * mz + 1.2 * same_xy + 0.45 * parity
        elif mech == "M9":
            score = -2.0 - 1.65 * mixed_xy - 0.85 * mz + 0.55 * prep_product
        elif mech == "M10":
            score = 2.0 + 2.1 * same_xy - 1.55 * mixed_xy - 1.45 * mz + 0.45 * _axis_indicator(tokens["meas_left"], "X")
        else:
            score = -2.05 * mz + 1.85 * parity * (mx + my + 0.25) - 1.15 * prep_product
        values.append(float(0.92 * np.tanh(score)))
    return np.asarray(values, dtype=np.float32)


def _apply_pair_correlation_overlays(
    observations_gpu,
    records: list[dict[str, object]],
    probe_names: list[str],
    *,
    generator,
    response_model: str,
) -> dict[str, object]:
    import torch

    if _normalize_response_model(response_model) != "separability_v2":
        return {"enabled": False, "num_overlay_entries": 0, "num_records": 0}
    probe_ids: list[int] = []
    left_ids: list[int] = []
    right_ids: list[int] = []
    strengths: list[float] = []
    record_count = 0
    for record in records:
        qubits = [int(value) for value in record.get("qubits", [])]
        if len(qubits) < 2:
            continue
        probe_indices = [int(value) for value in record.get("probe_indices", [])]
        local_probe_names = [probe_names[probe_idx] for probe_idx in probe_indices if 0 <= probe_idx < len(probe_names)]
        profile = _record_pair_correlation_profile(record, local_probe_names, response_model=response_model)
        left = min(qubits)
        right = max(qubits)
        used = 0
        for local_idx, probe_idx in enumerate(probe_indices):
            if probe_idx < 0 or probe_idx >= len(probe_names):
                continue
            strength = float(profile[local_idx % profile.size])
            if abs(strength) < 0.02:
                continue
            probe_ids.append(int(probe_idx))
            left_ids.append(int(left))
            right_ids.append(int(right))
            strengths.append(strength)
            used += 1
        if used:
            record_count += 1
    if not strengths:
        return {"enabled": True, "num_overlay_entries": 0, "num_records": 0}
    device = observations_gpu.device
    probe_t = torch.as_tensor(probe_ids, dtype=torch.long, device=device)
    left_t = torch.as_tensor(left_ids, dtype=torch.long, device=device)
    right_t = torch.as_tensor(right_ids, dtype=torch.long, device=device)
    strength_t = torch.as_tensor(strengths, dtype=torch.float32, device=device)
    current_right = observations_gpu[probe_t, :, right_t]
    left_values = observations_gpu[probe_t, :, left_t]
    target_right = torch.where(strength_t[:, None] >= 0.0, left_values, torch.logical_not(left_values))
    mask = torch.rand((len(strengths), observations_gpu.shape[1]), dtype=torch.float32, device=device, generator=generator) < torch.abs(strength_t)[:, None]
    observations_gpu[probe_t, :, right_t] = torch.where(mask, target_right, current_right)
    return {
        "enabled": True,
        "num_overlay_entries": int(len(strengths)),
        "num_records": int(record_count),
        "max_abs_strength": float(max(abs(value) for value in strengths)),
        "mean_abs_strength": float(np.mean(np.abs(np.asarray(strengths, dtype=np.float64)))),
    }


def build_self_distinguishability_preflight(
    records: list[dict[str, object]],
    probe_names: list[str],
    *,
    response_model: str,
    num_qubits: int,
    theta: float = 0.18,
    configured_circuit_depth: int = 1,
) -> dict[str, object]:
    model = _normalize_response_model(response_model)
    rows = []
    for idx, record in enumerate(records):
        probe_indices = [int(value) for value in record.get("probe_indices", [])]
        local_probe_names = [probe_names[probe_idx] for probe_idx in probe_indices if 0 <= probe_idx < len(probe_names)]
        if model == "born_local":
            table = _record_probability_table(record, local_probe_names, response_model=model, num_qubits=int(num_qubits), theta=float(theta))
            probabilities = np.mean(table, axis=1)
            outcome_table, _ = _record_born_local_tables(record, local_probe_names, num_qubits=int(num_qubits), theta=float(theta))
            correlations = np.asarray([outcome_zz_correlation(row) for row in outcome_table], dtype=np.float32)
        else:
            probabilities = _record_probability_profile(record, local_probe_names, response_model=model)
            correlations = _record_pair_correlation_profile(record, local_probe_names, response_model=model)
        expected = _expected_response_vector(probabilities, correlations, local_probe_names)
        rows.append(
            {
                "location_id": int(record.get("location_id", idx)),
                "oracle_label_evaluator_only": str(record.get("oracle_label", "")),
                "circuit_id": int(record.get("circuit_id", 0)),
                "instruction": str(record.get("instruction", "")),
                "qubits": [int(value) for value in record.get("qubits", [])],
                "expected_response": expected,
            }
        )
    labels = sorted({str(row["oracle_label_evaluator_only"]) for row in rows}, key=_mechanism_sort_key)
    centers = {
        label: np.mean([np.asarray(row["expected_response"], dtype=np.float64) for row in rows if row["oracle_label_evaluator_only"] == label], axis=0)
        for label in labels
    }
    pairwise = {}
    for left_idx, left in enumerate(labels):
        for right in labels[left_idx + 1 :]:
            pairwise[f"{left}__{right}"] = float(np.linalg.norm(centers[left] - centers[right]))
    alias_margins = {}
    for group_name, group_labels in SELF_DISTINGUISHABILITY_ALIAS_GROUPS.items():
        local = {}
        active = [label for label in group_labels if label in centers]
        for left_idx, left in enumerate(active):
            for right in active[left_idx + 1 :]:
                local[f"{left}__{right}"] = pairwise.get(f"{left}__{right}", pairwise.get(f"{right}__{left}", 0.0))
        alias_margins[group_name] = local
    low_margin = sorted(pairwise.items(), key=lambda item: item[1])[:20]
    return {
        "schema": "scope_static_local_observable_self_distinguishability_preflight_v1",
        "teacher_model": LOCAL_OBSERVABLE_TEACHER_MODEL,
        "local_observable_response_model": model,
        "num_records": int(len(records)),
        "num_qubits": int(num_qubits),
        "num_probes": int(len(probe_names)),
        "configured_circuit_depth": int(configured_circuit_depth),
        "effective_circuit_depth": int(_effective_circuit_depth(model, configured_circuit_depth)),
        "circuit_depth_semantics": _circuit_depth_semantics(model),
        "expected_response_feature_names": _expected_response_feature_names(),
        "alias_pairwise_margins": alias_margins,
        "lowest_pairwise_margins": [{"pair": key, "distance": float(value)} for key, value in low_margin],
        "minimum_pairwise_margin": float(min(pairwise.values())) if pairwise else 0.0,
        "mean_pairwise_margin": float(np.mean(list(pairwise.values()))) if pairwise else 0.0,
    }


def _expected_response_vector(probabilities: np.ndarray, correlations: np.ndarray, probe_names: list[str]) -> list[float]:
    p = np.asarray(probabilities, dtype=np.float64)
    c = np.asarray(correlations, dtype=np.float64)
    if p.size == 0:
        p = np.asarray([0.5], dtype=np.float64)
    if c.size == 0:
        c = np.zeros_like(p)
    axis_means = [_probe_subset_mean(p, probe_names, meas_axis=axis) for axis in ("X", "Y", "Z")]
    prep_means = [_probe_subset_mean(p, probe_names, prep_axis=axis) for axis in ("X", "Y", "Z")]
    parity_means = [_probe_subset_mean(p, probe_names, parity=parity) for parity in ("even", "odd")]
    corr_axis = [_probe_subset_mean(c, probe_names, meas_axis=axis) for axis in ("X", "Y", "Z")]
    corr_parity = [_probe_subset_mean(c, probe_names, parity=parity) for parity in ("even", "odd")]
    return [
        float(np.mean(p)),
        float(np.std(p)),
        float(np.min(p)),
        float(np.max(p)),
        *axis_means,
        *prep_means,
        *parity_means,
        float(np.mean(c)),
        float(np.std(c)),
        float(np.min(c)),
        float(np.max(c)),
        *corr_axis,
        *corr_parity,
    ]


def _expected_response_feature_names() -> list[str]:
    return [
        "p_mean",
        "p_std",
        "p_min",
        "p_max",
        "p_meas_x",
        "p_meas_y",
        "p_meas_z",
        "p_prep_x",
        "p_prep_y",
        "p_prep_z",
        "p_even",
        "p_odd",
        "corr_mean",
        "corr_std",
        "corr_min",
        "corr_max",
        "corr_meas_x",
        "corr_meas_y",
        "corr_meas_z",
        "corr_even",
        "corr_odd",
    ]


def _probe_subset_mean(values: np.ndarray, probe_names: list[str], *, meas_axis: str | None = None, prep_axis: str | None = None, parity: str | None = None) -> float:
    selected = []
    for idx, name in enumerate(probe_names):
        tokens = _probe_tokens(name)
        if meas_axis is not None and meas_axis not in {tokens["meas_left"], tokens["meas_right"]}:
            continue
        if prep_axis is not None and prep_axis not in {tokens["prep_left"][0], tokens["prep_right"][0]}:
            continue
        if parity is not None and parity != tokens["parity"]:
            continue
        selected.append(float(values[idx % values.size]))
    return float(np.mean(selected)) if selected else float(np.mean(values))


def _branch_specific_probability_profile(spec, raw: np.ndarray, probe_names: list[str]) -> np.ndarray:
    mech = str(spec.mechanism_id)
    raw_profile = _fingerprint_response_profile(raw, probe_names)
    scores = []
    for name in probe_names:
        tokens = _probe_tokens(name)
        if mech in READOUT_ALIAS_GROUP:
            score = _readout_score(mech, tokens)
        elif mech in RZZ_ALIAS_GROUP:
            score = _rzz_gate_score(mech, tokens)
        elif str(spec.instruction or "").lower() == "reset" or mech in {"M17", "M18"}:
            score = _prep_reset_score(mech, tokens)
        else:
            score = _single_gate_score(mech, tokens)
        score += 1.65 * _raw_channel_anchor_score(raw, tokens)
        template_weight = 0.0 if mech in RZZ_ALIAS_GROUP else 5.0
        score += template_weight * _mechanism_template_score(mech, tokens)
        scores.append(score)
    score_arr = np.asarray(scores, dtype=np.float64)
    score_arr = score_arr / max(1.0, float(np.std(score_arr)))
    score_arr = _mechanism_response_scale(mech) * score_arr + _mechanism_response_bias(mech)
    raw_centered = np.asarray(raw_profile, dtype=np.float64) - float(np.mean(raw_profile))
    combined = score_arr + 0.35 * raw_centered / max(0.05, float(np.std(raw_centered)))
    return 0.5 + 0.44 * np.tanh(combined)


def _mechanism_response_bias(mechanism_id: str) -> float:
    explicit = {
        "M8": -1.75,
        "M9": -0.55,
        "M10": 0.65,
        "M12": 1.75,
    }
    if mechanism_id in explicit:
        return explicit[mechanism_id]
    idx = _mechanism_index(mechanism_id)
    if idx is None:
        return 0.0
    if 0 <= idx < 20:
        rank = (7 * idx) % 20
        return float(-1.9 + 3.8 * rank / 19.0)
    return float(1.15 * np.sin(1.61803398875 * float(idx + 1)))


def _mechanism_response_scale(mechanism_id: str) -> float:
    explicit = {
        "M8": 0.76,
        "M9": 0.96,
        "M10": 1.16,
        "M12": 1.36,
    }
    if mechanism_id in explicit:
        return explicit[mechanism_id]
    idx = _mechanism_index(mechanism_id)
    if idx is None:
        return 1.0
    if 0 <= idx < 20:
        rank = (11 * idx + 3) % 20
        return float(0.72 + 0.56 * rank / 19.0)
    return float(1.0 + 0.32 * np.cos(2.41421356237 * float(idx + 1)))


def _raw_channel_anchor_score(raw: np.ndarray, tokens: dict[str, str]) -> float:
    values = np.asarray(raw, dtype=np.float64).reshape(-1)
    values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
    if values.size == 0:
        values = np.zeros(1, dtype=np.float64)
    centered = values - float(np.mean(values))
    scale = float(np.std(centered))
    if scale < 1e-9:
        scale = 1.0
    coords = _response_coordinates(centered / scale, count=12)
    mx = 0.5 * (_axis_indicator(tokens["meas_left"], "X") + _axis_indicator(tokens["meas_right"], "X"))
    my = 0.5 * (_axis_indicator(tokens["meas_left"], "Y") + _axis_indicator(tokens["meas_right"], "Y"))
    mz = 0.5 * (_axis_indicator(tokens["meas_left"], "Z") + _axis_indicator(tokens["meas_right"], "Z"))
    prep_x = 0.5 * (_prep_axis_signed(tokens["prep_left"], "X") + _prep_axis_signed(tokens["prep_right"], "X"))
    prep_y = 0.5 * (_prep_axis_signed(tokens["prep_left"], "Y") + _prep_axis_signed(tokens["prep_right"], "Y"))
    prep_z = 0.5 * (_prep_axis_signed(tokens["prep_left"], "Z") + _prep_axis_signed(tokens["prep_right"], "Z"))
    parity = _parity_sign(tokens["parity"])
    prep_product = _prep_sign(tokens["prep_left"]) * _prep_sign(tokens["prep_right"])
    same_xy = 1.0 if tokens["meas_left"] == tokens["meas_right"] and tokens["meas_left"] in {"X", "Y"} else -0.25
    mixed_xy = 1.0 if {tokens["meas_left"], tokens["meas_right"]} == {"X", "Y"} else -0.25
    features = np.asarray(
        [
            mx,
            my,
            mz,
            prep_x,
            prep_y,
            prep_z,
            parity,
            prep_product,
            same_xy,
            mixed_xy,
            parity * mx,
            parity * mz,
        ],
        dtype=np.float64,
    )
    return float(np.dot(coords, features) / np.sqrt(float(features.size)))


def _mechanism_template_score(mechanism_id: str, tokens: dict[str, str]) -> float:
    idx = _mechanism_index(mechanism_id)
    if idx is None:
        return 0.0
    mx = 0.5 * (_axis_indicator(tokens["meas_left"], "X") + _axis_indicator(tokens["meas_right"], "X"))
    my = 0.5 * (_axis_indicator(tokens["meas_left"], "Y") + _axis_indicator(tokens["meas_right"], "Y"))
    mz = 0.5 * (_axis_indicator(tokens["meas_left"], "Z") + _axis_indicator(tokens["meas_right"], "Z"))
    prep_x = 0.5 * (_prep_axis_signed(tokens["prep_left"], "X") + _prep_axis_signed(tokens["prep_right"], "X"))
    prep_y = 0.5 * (_prep_axis_signed(tokens["prep_left"], "Y") + _prep_axis_signed(tokens["prep_right"], "Y"))
    prep_z = 0.5 * (_prep_axis_signed(tokens["prep_left"], "Z") + _prep_axis_signed(tokens["prep_right"], "Z"))
    parity = _parity_sign(tokens["parity"])
    prep_product = _prep_sign(tokens["prep_left"]) * _prep_sign(tokens["prep_right"])
    same_axis = 1.0 if tokens["meas_left"] == tokens["meas_right"] else -0.35
    mixed_xy = 1.0 if {tokens["meas_left"], tokens["meas_right"]} == {"X", "Y"} else -0.35
    features = np.asarray(
        [
            1.0,
            mx,
            my,
            mz,
            prep_x,
            prep_y,
            prep_z,
            parity,
            prep_product,
            same_axis,
            mixed_xy,
            mx * prep_x,
            my * prep_y,
            mz * prep_z,
            parity * mx,
            parity * my,
            parity * mz,
        ],
        dtype=np.float64,
    )
    code = _mechanism_code(idx, count=int(features.size))
    return float(np.dot(code, features) / np.sqrt(float(features.size)))


def _mechanism_code(index: int, *, count: int = 17) -> np.ndarray:
    dims = np.arange(1, int(count) + 1, dtype=np.float64)
    value = float(index + 1)
    raw = np.sin(12.9898 * value * dims + 0.37 * dims * dims) + 0.45 * np.cos(4.1414 * (value + 2.0) * (dims + 0.5))
    coords = np.where(raw >= 0.0, 1.0, -1.0).astype(np.float64)
    coords[0] = np.tanh((value - 9.5) / 4.0)
    return coords / max(1.0, float(np.linalg.norm(coords)))


def _readout_score(mech: str, tokens: dict[str, str]) -> float:
    mx = 0.5 * (_axis_indicator(tokens["meas_left"], "X") + _axis_indicator(tokens["meas_right"], "X"))
    my = 0.5 * (_axis_indicator(tokens["meas_left"], "Y") + _axis_indicator(tokens["meas_right"], "Y"))
    mz = 0.5 * (_axis_indicator(tokens["meas_left"], "Z") + _axis_indicator(tokens["meas_right"], "Z"))
    prep_z = 0.5 * (_prep_axis_signed(tokens["prep_left"], "Z") + _prep_axis_signed(tokens["prep_right"], "Z"))
    prep_product = _prep_sign(tokens["prep_left"]) * _prep_sign(tokens["prep_right"])
    parity = _parity_sign(tokens["parity"])
    if mech == "M1":
        return 2.6 * mz + 1.3 * prep_z + 0.35 * parity
    if mech == "M2":
        return -2.6 * mz - 1.3 * prep_z + 0.35 * parity
    if mech == "M3":
        return 2.25 * mx - 1.25 * my + 0.85 * prep_product - 0.25 * parity
    return -1.45 * mx + 2.35 * my + 1.75 * parity - 0.95 * prep_product


def _rzz_gate_score(mech: str, tokens: dict[str, str]) -> float:
    mx = 0.5 * (_axis_indicator(tokens["meas_left"], "X") + _axis_indicator(tokens["meas_right"], "X"))
    my = 0.5 * (_axis_indicator(tokens["meas_left"], "Y") + _axis_indicator(tokens["meas_right"], "Y"))
    mz = 0.5 * (_axis_indicator(tokens["meas_left"], "Z") + _axis_indicator(tokens["meas_right"], "Z"))
    same_xy = 1.0 if tokens["meas_left"] == tokens["meas_right"] and tokens["meas_left"] in {"X", "Y"} else 0.0
    mixed_xy = 1.0 if {tokens["meas_left"], tokens["meas_right"]} == {"X", "Y"} else 0.0
    prep_product = _prep_sign(tokens["prep_left"]) * _prep_sign(tokens["prep_right"])
    parity = _parity_sign(tokens["parity"])
    if mech == "M8":
        return 2.2 * mz + 1.15 * same_xy + 0.55 * parity
    if mech == "M9":
        return -1.8 * mixed_xy - 1.05 * mz + 1.1 * prep_product
    if mech == "M10":
        return 2.45 * same_xy + 1.05 * mx + 0.95 * my - 1.45 * mixed_xy - 1.55 * mz
    return 2.15 * parity + 1.65 * my - 1.7 * mz - 1.1 * prep_product - 0.35 * mx


def _single_gate_score(mech: str, tokens: dict[str, str]) -> float:
    mx = 0.5 * (_axis_indicator(tokens["meas_left"], "X") + _axis_indicator(tokens["meas_right"], "X"))
    my = 0.5 * (_axis_indicator(tokens["meas_left"], "Y") + _axis_indicator(tokens["meas_right"], "Y"))
    mz = 0.5 * (_axis_indicator(tokens["meas_left"], "Z") + _axis_indicator(tokens["meas_right"], "Z"))
    prep_x = 0.5 * (_prep_axis_signed(tokens["prep_left"], "X") + _prep_axis_signed(tokens["prep_right"], "X"))
    prep_y = 0.5 * (_prep_axis_signed(tokens["prep_left"], "Y") + _prep_axis_signed(tokens["prep_right"], "Y"))
    prep_z = 0.5 * (_prep_axis_signed(tokens["prep_left"], "Z") + _prep_axis_signed(tokens["prep_right"], "Z"))
    parity = _parity_sign(tokens["parity"])
    code = {
        "M0": (1.4, -0.3, 1.0, 0.6, 0.1, 0.2, -0.4),
        "M6": (2.3, -0.6, -0.2, 1.0, 0.2, -0.1, 0.3),
        "M7": (-0.4, 0.2, 2.4, -0.2, 0.1, 1.0, -0.3),
        "M4": (-0.8, 0.6, -1.9, -0.4, 0.2, -1.1, 0.7),
        "M15": (0.8, 1.7, -0.9, 0.9, -0.8, 0.5, -0.6),
        "M11": (-1.2, 1.2, 0.8, -0.5, 1.1, -0.4, 1.0),
        "M13": (1.8, 0.4, -1.2, 1.3, -0.2, -0.9, -1.0),
        "M5": (-0.5, -1.0, 2.2, -0.6, -0.2, 1.2, 0.6),
        "M14": (2.0, -1.1, 0.4, 0.3, 1.0, -0.5, -0.8),
        "M19": (0.6, -1.8, -0.6, -1.0, 1.2, 0.9, 0.5),
    }.get(mech, (0.9, -0.7, 0.4, 0.3, -0.2, 0.1, 0.5))
    return (
        code[0] * mx
        + code[1] * my
        + code[2] * mz
        + code[3] * prep_x
        + code[4] * prep_y
        + code[5] * prep_z
        + code[6] * parity
    )


def _prep_reset_score(mech: str, tokens: dict[str, str]) -> float:
    prep_x = 0.5 * (_prep_axis_signed(tokens["prep_left"], "X") + _prep_axis_signed(tokens["prep_right"], "X"))
    prep_y = 0.5 * (_prep_axis_signed(tokens["prep_left"], "Y") + _prep_axis_signed(tokens["prep_right"], "Y"))
    prep_z = 0.5 * (_prep_axis_signed(tokens["prep_left"], "Z") + _prep_axis_signed(tokens["prep_right"], "Z"))
    mz = 0.5 * (_axis_indicator(tokens["meas_left"], "Z") + _axis_indicator(tokens["meas_right"], "Z"))
    parity = _parity_sign(tokens["parity"])
    if mech == "M17":
        return 2.3 * prep_z - 1.0 * prep_x + 0.75 * mz + 0.35 * parity
    return -1.25 * prep_z + 2.1 * prep_x + 1.25 * prep_y - 0.8 * parity


def _fingerprint_response_profile(raw: np.ndarray, probe_names: list[str]) -> np.ndarray:
    values = np.asarray(raw, dtype=np.float64).reshape(-1)
    values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
    if values.size == 0:
        values = np.zeros(1, dtype=np.float64)
    centered = values - float(np.mean(values))
    scale = float(np.std(centered))
    if scale < 1e-9:
        scale = 1.0
    z = centered / scale
    magnitude = values / max(1e-9, float(np.linalg.norm(values)))
    probe_count = max(1, len(probe_names))
    probe = np.arange(1, probe_count + 1, dtype=np.float64)[:, None]
    feature = np.arange(1, values.size + 1, dtype=np.float64)[None, :]
    oscillatory = np.sin(0.071 * probe * feature) + np.cos(0.113 * probe * (feature + 0.5))
    absolute = np.cos(0.037 * (probe + 3.0) * (feature + 1.0))
    signature = (oscillatory @ z + 0.8 * (absolute @ magnitude)) / np.sqrt(float(values.size))
    phase = float(np.sum(z[: min(8, z.size)]))
    signature = signature.reshape(-1) + 0.3 * np.sin(0.173 * probe.reshape(-1) + phase)
    signature = signature / max(1.0, float(np.std(signature)))
    mechanism_bias = 0.025 * np.tanh(float(np.mean(values) + np.std(values)))
    response_coords = _response_coordinates(z, count=18)
    design = np.asarray([_probe_design_score(name, response_coords) for name in probe_names], dtype=np.float64)
    design = design / max(1.0, float(np.std(design)))
    combined = 0.45 * signature + 0.9 * design
    return 0.5 + mechanism_bias + 0.42 * np.tanh(combined)


def _response_coordinates(z: np.ndarray, *, count: int) -> np.ndarray:
    values = np.asarray(z, dtype=np.float64).reshape(-1)
    feature = np.arange(1, values.size + 1, dtype=np.float64)[None, :]
    coord = np.arange(1, int(count) + 1, dtype=np.float64)[:, None]
    weights = np.sin(0.191 * coord * feature) + np.cos(0.127 * (coord + 2.0) * (feature + 0.5))
    out = (weights @ values) / np.sqrt(float(values.size))
    return np.tanh(out.reshape(-1))


def _probe_design_score(name: str, coords: np.ndarray) -> float:
    tokens = _probe_tokens(name)
    score = 0.0
    axis = {"X": 0, "Y": 1, "Z": 2}
    score += 0.55 * coords[axis[tokens["prep_left"][0]]]
    score += 0.35 * coords[3 + axis[tokens["prep_right"][0]]]
    score += 0.45 * _prep_sign(tokens["prep_left"]) * coords[6 + axis[tokens["prep_left"][0]]]
    score += 0.30 * _prep_sign(tokens["prep_right"]) * coords[9 + axis[tokens["prep_right"][0]]]
    score += 0.65 * coords[12 + axis[tokens["meas_left"]]]
    score += 0.45 * coords[15 + axis[tokens["meas_right"]]]
    if tokens["parity"] == "even":
        score += 0.25 * float(np.mean(coords[:9]))
    elif tokens["parity"] == "odd":
        score -= 0.25 * float(np.mean(coords[9:]))
    return float(score)


def _probe_tokens(name: str) -> dict[str, str]:
    base = str(name).split(":", 1)[1] if ":" in str(name) else str(name)
    match = re.match(r"rzz_tomo_p([XYZ][pm])([XYZ][pm])_m([XYZ])([XYZ])_(even|odd)$", base)
    if match is None:
        return {"prep_left": "Zp", "prep_right": "Zp", "meas_left": "Z", "meas_right": "Z", "parity": "even"}
    prep_left, prep_right, meas_left, meas_right, parity = match.groups()
    return {
        "prep_left": prep_left,
        "prep_right": prep_right,
        "meas_left": meas_left,
        "meas_right": meas_right,
        "parity": parity,
    }


def _axis_indicator(axis: str, target: str) -> float:
    return 1.0 if str(axis).upper() == str(target).upper() else -0.35


def _prep_sign(prep: str) -> float:
    return -1.0 if str(prep).endswith("m") else 1.0


def _prep_axis_signed(prep: str, axis: str) -> float:
    return _prep_sign(prep) if str(prep).startswith(str(axis).upper()) else -0.25


def _parity_sign(parity: str) -> float:
    return 1.0 if str(parity) == "even" else -1.0


def _normalize_response_model(value: str) -> str:
    text = str(value).strip().lower().replace("-", "_")
    aliases = {
        "": "separability_v2",
        "v1": "separability_v1",
        "separability_v1": "separability_v1",
        "legacy": "separability_v1",
        "v2": "separability_v2",
        "separability_v2": "separability_v2",
        "branch_specific": "separability_v2",
        "born": "born_local",
        "born_local": "born_local",
        "born_local_v1": "born_local",
        "bornlocal": "born_local",
        "born-rule-local": "born_local",
        "born_rule_local": "born_local",
        "phyc2_born_local": "born_local",
    }
    if text not in aliases:
        raise ValueError("local_observable_response_model must be 'separability_v1', 'separability_v2', or 'born_local'")
    return aliases[text]


def _effective_circuit_depth(response_model: str, configured_circuit_depth: int) -> int:
    if _normalize_response_model(response_model) == "born_local":
        return BORN_LOCAL_EFFECTIVE_CIRCUIT_DEPTH
    return max(1, int(configured_circuit_depth))


def _circuit_depth_semantics(response_model: str) -> str:
    if _normalize_response_model(response_model) == "born_local":
        return BORN_LOCAL_DEPTH_SEMANTICS
    return "configured circuit_depth is artifact provenance for the engineered local-observable response model"


def _filter_born_local_supported_records(records: list[dict[str, object]]) -> list[dict[str, object]]:
    supported = set(BORN_LOCAL_SUPPORTED_MECHANISMS)
    return [record for record in records if str(record.get("oracle_label", "")) in supported]


def _born_local_scope_audit(records: list[dict[str, object]]) -> dict[str, object]:
    supported = set(BORN_LOCAL_SUPPORTED_MECHANISMS)
    requested = sorted({str(record.get("oracle_label", "")) for record in records}, key=_mechanism_sort_key)
    excluded = [label for label in requested if label not in supported]
    return {
        "schema": "scope_static_stage2e_born_local_scope_v1",
        "stage": "Stage 2E.1",
        "teacher_model": "PHYC2-Born-local minimal teacher",
        "supported_mechanisms": list(BORN_LOCAL_SUPPORTED_MECHANISMS),
        "requested_mechanisms": requested,
        "excluded_unsupported_mechanisms": excluded,
        "unsupported_mechanism_reasons": {
            label: BORN_LOCAL_UNSUPPORTED_MECHANISM_REASONS.get(label, "not in Stage 2E.1 Born-local thin-slice scope")
            for label in excluded
        },
        "num_supported_records": int(sum(1 for record in records if str(record.get("oracle_label", "")) in supported)),
        "num_excluded_records": int(sum(1 for record in records if str(record.get("oracle_label", "")) not in supported)),
    }


def _sample_born_local_joint_entries(
    observations_gpu,
    entries: list[dict[str, object]],
    *,
    shots: int,
    generator,
) -> dict[str, object]:
    import torch

    if not entries:
        return {"enabled": True, "num_entries": 0, "num_records": 0}
    device = observations_gpu.device
    num_entries = 0
    for entry in entries:
        probe_indices = [int(value) for value in entry["probe_indices"]]
        if not probe_indices:
            continue
        left = int(entry["left"])
        right = int(entry["right"])
        if left < 0 or right < 0 or left >= observations_gpu.shape[2] or right >= observations_gpu.shape[2]:
            continue
        outcomes = torch.as_tensor(entry["outcomes"], dtype=torch.float32, device=device)
        cdf = torch.cumsum(outcomes, dim=1)
        cdf[:, -1] = 1.0
        random = torch.rand((len(probe_indices), int(shots)), dtype=torch.float32, device=device, generator=generator)
        sampled = torch.sum(random[:, :, None] > cdf[:, None, :], dim=2)
        probe_t = torch.as_tensor(probe_indices, dtype=torch.long, device=device)
        observations_gpu[probe_t, :, left] = sampled >= 2
        observations_gpu[probe_t, :, right] = torch.remainder(sampled, 2) == 1
        num_entries += len(probe_indices)
    return {
        "enabled": True,
        "num_entries": int(num_entries),
        "num_records": int(len(entries)),
        "method": "direct_categorical_sampling_from_born_local_joint_povm",
    }


def _mechanism_sort_key(name: str) -> tuple[int, str]:
    text = str(name)
    if text.startswith("M") and text[1:].isdigit():
        return (int(text[1:]), text)
    return (10_000, text)


def _mechanism_index(name: str) -> int | None:
    text = str(name)
    if text.startswith("M") and text[1:].isdigit():
        return int(text[1:])
    return None


def _counts(values) -> dict[str, int]:
    out: dict[str, int] = {}
    for value in values:
        out[str(value)] = out.get(str(value), 0) + 1
    return out


def _mechanism_instance_counts(config: dict[str, object], *, default_count: int) -> dict[str, int]:
    raw = config.get("mechanism_instance_counts", {})
    if not isinstance(raw, dict) or not raw:
        return {}
    counts: dict[str, int] = {}
    for key, value in raw.items():
        counts[str(key)] = max(0, int(value))
    enabled = {str(record["oracle_label"]) for record in _records_for_enabled_count_probe(config, default_count=default_count)}
    return {key: value for key, value in counts.items() if key in enabled}


def _records_for_enabled_count_probe(config: dict[str, object], *, default_count: int) -> list[dict[str, object]]:
    cfg = dict(config)
    cfg["balanced_min_instances_per_mechanism"] = max(2, int(default_count))
    return [{"oracle_label": spec.mechanism_id} for spec in _build_balanced_oracle_mechanisms(cfg)]


def _summary_markdown(summary: dict[str, object]) -> str:
    sampling = summary.get("sampling", {})
    if not isinstance(sampling, dict):
        sampling = {}
    return "\n".join(
        [
            "# PHYS1 Local Observable GPU Teacher",
            "",
            f"- Output: `{summary.get('output_dir')}`",
            f"- Qubits: `{summary.get('num_qubits')}`",
            f"- Configured circuit depth: `{summary.get('configured_circuit_depth')}`",
            f"- Effective circuit depth: `{summary.get('effective_circuit_depth')}`",
            f"- Probes: `{summary.get('num_probes')}`",
            f"- Shots: `{summary.get('shots')}`",
            f"- Sampling seconds: `{float(sampling.get('sampling_wall_clock_seconds', 0.0)):.6f}`",
            f"- Total seconds: `{float(sampling.get('total_wall_clock_seconds', 0.0)):.6f}`",
            "",
        ]
    )


def _json_safe(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    return value
