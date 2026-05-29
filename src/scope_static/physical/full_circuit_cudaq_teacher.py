from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Mapping

import numpy as np

from .channels import MechanismSpec, mechanism_channel, readout_bias_matrix
from .cptp_guardrail import build_cptp_guardrail_audit
from .mechanism_catalog import PREP_RESET_MECHANISM_IDS, READOUT_MECHANISM_IDS
from .layers import LAYER1_PREP
from .phyc1_contract import (
    FULL_CIRCUIT_CONTRACT_NOTE,
    FULL_CIRCUIT_DEPTH_SEMANTICS,
    FULL_CIRCUIT_MECHANISM_APPLICATION_CONVENTION,
    FULL_CIRCUIT_RZZ_GATE_SEMANTICS,
    FULL_CIRCUIT_TEACHER_MODEL,
    PHYC1_LEGACY_STAGE_NAME,
    READOUT_APPLICATION_CONVENTION,
    apply_full_circuit_depth_metadata,
    circuit_depth,
    counts_to_bit_matrix,
    full_circuit_depth_metadata,
    mechanism_counts,
    probe_names as phyc1_probe_names,
)
from .teacher import (
    _apply_measurement_basis_rotations,
    _apply_rzz_echo_block,
    _apply_rzz_minimal_sign_block,
    _apply_rzz_pauli_frame,
    _apply_rzz_tomography_block,
    _apply_rzz_tomography_preparation,
    _balanced_repetitions,
    _build_balanced_oracle_mechanisms,
    _drift_targets,
    _is_rzz_echo_probe,
    _is_rzz_minimal_sign_probe,
    _is_rzz_tomography_probe,
    _mechanism_set_contains,
    _merged_config,
    _probe_rzz_depth,
    _profile_rx_qubits,
    _profile_ry_qubits,
    _profile_rz_qubits,
    _single_targets,
    build_noise_application_audit,
    build_non_clifford_audit,
    build_probe_basis_manifest,
)

NOISE_MODEL_OPERATIONS = {"h", "s", "x", "y", "z", "rx", "ry", "rz", "mz", "r1", "u3"}


def generate_full_circuit_cudaq_teacher_dataset(
    config: dict[str, object] | None = None,
    *,
    output_dir: str | Path,
) -> dict[str, object]:
    """Generate PHYS1 artifacts from literal depth-d n-qubit CUDA-Q circuits.

    The sampled path is:

        rho_probe -> full n-qubit ideal schedule of depth d
        -> mechanism channels/readout -> sampled observations

    Checkpoints are written after each shot chunk and consolidated per probe
    circuit, so an interrupted run can resume without discarding completed GPU
    work.
    """

    cudaq = _cudaq()
    cfg = _merged_config(config)
    cfg["backend"] = "cudaq"
    cfg["physical_teacher_model"] = FULL_CIRCUIT_TEACHER_MODEL
    n = int(cfg.get("num_qubits", 5))
    shots = int(cfg.get("shots", 10_000))
    seed = int(cfg.get("seed", 0))
    depth = circuit_depth(cfg)
    theta = float(cfg.get("theta", 0.18))
    rzz_implementation = _rzz_implementation(cfg)
    cfg["full_circuit_cudaq_rzz_implementation"] = rzz_implementation
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = output / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    target_audit = _configure_cudaq_target(cudaq, cfg)
    mechanisms, repetitions, sampling_contract = _build_full_circuit_oracle_mechanisms(cfg)
    base_probe_names = phyc1_probe_names(str(cfg.get("probe_set", "base")))
    probe_names = [f"c{circuit_id}:{name}" for circuit_id in range(repetitions) for name in base_probe_names]
    records = _mechanism_records(mechanisms)
    specs_by_group: dict[int, list[MechanismSpec]] = {}
    for spec in mechanisms:
        specs_by_group.setdefault(int(spec.circuit_id), []).append(spec)

    apply_full_circuit_depth_metadata(cfg, depth)
    cfg["sampling_contract"] = sampling_contract
    static_artifacts = _write_static_artifacts(
        output,
        cfg=cfg,
        mechanisms=mechanisms,
        records=records,
        probe_names=probe_names,
        num_qubits=n,
        circuit_depth=depth,
        target_audit=target_audit,
    )

    shot_batch_size = _shot_batch_size(cfg, shots=shots, num_qubits=n, circuit_depth=depth)
    verbose = bool(cfg.get("full_circuit_cudaq_progress_logging", True))
    stop_after = cfg.get("full_circuit_cudaq_interrupt_after_completed_probes")
    stop_after_count = None if stop_after is None else int(stop_after)
    started = time.perf_counter()
    progress = _initial_progress(
        cfg,
        output=output,
        target_audit=target_audit,
        num_qubits=n,
        circuit_depth=depth,
        shots=shots,
        repetitions=repetitions,
        probe_names=probe_names,
        shot_batch_size=shot_batch_size,
    )

    channel_cache = {
        circuit_id: _mechanism_channels_by_location(
            cudaq,
            specs,
            mode=str(cfg.get("full_circuit_cudaq_noise_mode", "hybrid")),
            rzz_implementation=rzz_implementation,
        )
        for circuit_id, specs in specs_by_group.items()
    }
    sample_records: list[dict[str, object]] = []
    materialize_seconds = 0.0
    sampling_seconds = 0.0
    readout_seconds = 0.0
    checkpoint_write_seconds = 0.0
    skipped_probe_circuits = 0
    resumed_shot_chunks = 0
    resumed_shots = 0
    completed_now = 0
    total = len(probe_names)

    _write_progress(output, progress)
    _log(
        verbose,
        (
            "[full-circuit-cudaq] start "
            f"target={target_audit.get('cudaq_target')} qubits={n} depth={depth} "
            f"shots={shots} probes={total} shot_batch_size={shot_batch_size} "
            f"rzz_implementation={rzz_implementation}"
        ),
    )
    for circuit_id in range(repetitions):
        group_specs = specs_by_group.get(circuit_id, [])
        inline_channels, noise_model, has_noise_model_channels = channel_cache.get(circuit_id, ({}, cudaq.NoiseModel(), False))
        sample_noise_model = noise_model if inline_channels or has_noise_model_channels else None
        for local_probe_idx, base_probe in enumerate(base_probe_names):
            probe_index = circuit_id * len(base_probe_names) + local_probe_idx
            consolidated = _probe_checkpoint_path(checkpoint_dir, probe_index)
            loaded = _load_probe_checkpoint_metadata(consolidated, probe_index=probe_index, shots=shots, num_qubits=n)
            if loaded is not None:
                skipped_probe_circuits += 1
                sample_records.append({**loaded, "resumed_from_checkpoint": True})
                progress.update(
                    {
                        "completed_probe_circuits": int(probe_index + 1),
                        "skipped_resumed_probe_circuits": int(skipped_probe_circuits),
                        "updated_wall_clock_seconds": float(time.perf_counter() - started),
                    }
                )
                _write_progress(output, progress)
                _log(verbose, f"[full-circuit-cudaq] resume-skip probe={probe_index + 1}/{total} name={probe_names[probe_index]}")
                continue

            chunk_paths, contiguous_shots = _contiguous_chunk_paths(
                checkpoint_dir,
                probe_index=probe_index,
                shots=shots,
                num_qubits=n,
            )
            if chunk_paths:
                resumed_shot_chunks += len(chunk_paths)
                resumed_shots += int(contiguous_shots)
                _log(
                    verbose,
                    (
                        "[full-circuit-cudaq] resume-partial "
                        f"probe={probe_index + 1}/{total} name={probe_names[probe_index]} "
                        f"shots={contiguous_shots}/{shots}"
                    ),
                )

            build_started = time.perf_counter()
            kernel = _build_cudaq_kernel(
                cudaq,
                cfg,
                probe_name=base_probe,
                inline_channels=inline_channels,
                num_qubits=n,
                circuit_depth=depth,
                theta=theta,
            )
            materialize_seconds += time.perf_counter() - build_started
            chunk_unique_outcomes: list[int] = []
            chunk_count = len(chunk_paths)
            for start in range(int(contiguous_shots), shots, shot_batch_size):
                end = min(shots, start + shot_batch_size)
                chunk_shots = int(end - start)
                _set_cudaq_seed(cudaq, _chunk_seed(seed=seed, probe_index=probe_index, start=start))
                sample_started = time.perf_counter()
                counts = cudaq.sample(kernel, shots_count=chunk_shots, noise_model=sample_noise_model)
                sampling_seconds += time.perf_counter() - sample_started
                count_items = dict(counts.items())
                chunk_unique_outcomes.append(int(len(count_items)))
                rows = counts_to_bit_matrix(count_items, shots=chunk_shots, num_bits=n)
                readout_started = time.perf_counter()
                _apply_readout_mechanisms(
                    rows,
                    group_specs,
                    rng=np.random.default_rng(_chunk_seed(seed=seed + 17, probe_index=probe_index, start=start)),
                )
                readout_seconds += time.perf_counter() - readout_started
                checkpoint_started = time.perf_counter()
                chunk_path = _write_chunk_checkpoint(
                    checkpoint_dir,
                    probe_index=probe_index,
                    chunk_index=chunk_count,
                    start=start,
                    end=end,
                    rows=rows,
                    metadata={
                        "circuit_id": int(circuit_id),
                        "probe_index": int(probe_index),
                        "probe_name": str(probe_names[probe_index]),
                        "base_probe_name": str(base_probe),
                        "shots": int(shots),
                        "num_qubits": int(n),
                        "configured_circuit_depth": int(depth),
                        "effective_circuit_depth": int(depth),
                        "rzz_implementation": rzz_implementation,
                        "cudaq_target": target_audit.get("cudaq_target"),
                    },
                )
                checkpoint_write_seconds += time.perf_counter() - checkpoint_started
                chunk_paths.append(chunk_path)
                chunk_count += 1
                progress.update(
                    {
                        "active_probe_index": int(probe_index),
                        "active_probe_name": str(probe_names[probe_index]),
                        "completed_shots_in_active_probe": int(end),
                        "completed_shot_chunks": int(progress.get("completed_shot_chunks", 0)) + 1,
                        "resumed_shot_chunks": int(resumed_shot_chunks),
                        "resumed_shots": int(resumed_shots),
                        "updated_wall_clock_seconds": float(time.perf_counter() - started),
                    }
                )
                _write_progress(output, progress)
                _log(
                    verbose,
                    (
                        "[full-circuit-cudaq] chunk "
                        f"probe={probe_index + 1}/{total} name={probe_names[probe_index]} "
                        f"shots={end}/{shots} unique={len(count_items)}"
                    ),
                )

            checkpoint_started = time.perf_counter()
            probe_metadata = {
                "circuit_id": int(circuit_id),
                "probe_index": int(probe_index),
                "probe_name": str(probe_names[probe_index]),
                "base_probe_name": str(base_probe),
                "shots": int(shots),
                "num_qubits": int(n),
                "configured_circuit_depth": int(depth),
                "effective_circuit_depth": int(depth),
                "rzz_implementation": rzz_implementation,
                "chunk_count": int(chunk_count),
                "unique_outcomes_max": int(max(chunk_unique_outcomes) if chunk_unique_outcomes else 0),
                "checkpoint_path": str(consolidated),
                "resumed_from_checkpoint": False,
            }
            sample_records.append(_consolidate_probe_checkpoint(chunk_paths, consolidated, probe_metadata, shots=shots, num_qubits=n))
            checkpoint_write_seconds += time.perf_counter() - checkpoint_started
            completed_now += 1
            progress.update(
                {
                    "completed_probe_circuits": int(probe_index + 1),
                    "completed_probe_circuits_this_run": int(completed_now),
                    "skipped_resumed_probe_circuits": int(skipped_probe_circuits),
                    "completed_shots_in_active_probe": int(shots),
                    "updated_wall_clock_seconds": float(time.perf_counter() - started),
                }
            )
            _write_progress(output, progress)
            _log(verbose, f"[full-circuit-cudaq] complete probe={probe_index + 1}/{total} name={probe_names[probe_index]}")
            if stop_after_count is not None and completed_now >= stop_after_count:
                progress["interrupted_for_test_after_probe_circuits"] = int(completed_now)
                _write_progress(output, progress)
                raise KeyboardInterrupt("full_circuit_cudaq_interrupt_after_completed_probes reached")

    assembly_started = time.perf_counter()
    observations = _assemble_observations(checkpoint_dir, num_probes=len(probe_names), shots=shots, num_qubits=n)
    assembly_seconds = time.perf_counter() - assembly_started
    np.savez(
        output / "observations.npz",
        observations=observations,
        probe_names=np.asarray(probe_names),
        shots=np.asarray([shots], dtype=np.int64),
    )
    total_seconds = time.perf_counter() - started
    sampling_audit = {
        "schema": "scope_static_full_circuit_cudaq_sampling_audit_v1",
        "public_layer": LAYER1_PREP.metadata(artifact_stage=PHYC1_LEGACY_STAGE_NAME, substage="full_circuit_cudaq_sampling"),
        "teacher_model": FULL_CIRCUIT_TEACHER_MODEL,
        "physical_teacher_model": FULL_CIRCUIT_TEACHER_MODEL,
        "backend": "cudaq",
        "cudaq_target": target_audit.get("cudaq_target"),
        "cudaq_target_description": target_audit.get("cudaq_target_description"),
        "cudaq_target_options": target_audit.get("cudaq_target_options"),
        "require_gpu": bool(target_audit.get("require_gpu", True)),
        "cpu_fallback_allowed": bool(target_audit.get("cpu_fallback_allowed", False)),
        "num_qubits": int(n),
        "num_physical_qubits": int(n),
        "num_observation_slots": int(n),
        **full_circuit_depth_metadata(depth),
        "rzz_implementation": rzz_implementation,
        "rzz_gate_semantics": FULL_CIRCUIT_RZZ_GATE_SEMANTICS,
        "shots": int(shots),
        "shot_batch_size": int(shot_batch_size),
        "num_probe_circuits": int(len(probe_names)),
        "num_circuit_id_groups": int(repetitions),
        "completed_probe_circuits": int(len(probe_names)),
        "completed_circuit_id_groups": int(repetitions),
        "skipped_resumed_probe_circuits": int(skipped_probe_circuits),
        "resumed_shot_chunks": int(resumed_shot_chunks),
        "resumed_shots": int(resumed_shots),
        "materialization_wall_clock_seconds": float(materialize_seconds),
        "sampling_wall_clock_seconds": float(sampling_seconds),
        "readout_postprocess_wall_clock_seconds": float(readout_seconds),
        "checkpoint_write_wall_clock_seconds": float(checkpoint_write_seconds),
        "assembly_wall_clock_seconds": float(assembly_seconds),
        "total_wall_clock_seconds": float(total_seconds),
        "sample_records": sample_records,
        "sampling_contract": sampling_contract,
        "checkpoint_dir": str(checkpoint_dir),
        "progress_artifact": str(output / "sampling_progress.json"),
        "noise_application_mode": str(cfg.get("full_circuit_cudaq_noise_mode", "hybrid")),
        "noise_model_excluded_operations": _noise_model_excluded_operations(rzz_implementation),
        "mechanism_application_convention": FULL_CIRCUIT_MECHANISM_APPLICATION_CONVENTION,
        "contract_note": FULL_CIRCUIT_CONTRACT_NOTE,
        "metrics_are_wall_clock": True,
    }
    (output / "sampling_audit.json").write_text(json.dumps(_json_safe(sampling_audit), indent=2, sort_keys=True) + "\n")
    progress.update(
        {
            "completed": True,
            "completed_probe_circuits": int(len(probe_names)),
            "updated_wall_clock_seconds": float(total_seconds),
            "sampling_audit": str(output / "sampling_audit.json"),
        }
    )
    _write_progress(output, progress)
    summary = {
        "schema": "scope_static_full_circuit_cudaq_teacher_v1",
        "stage": PHYC1_LEGACY_STAGE_NAME,
        "public_layer": LAYER1_PREP.metadata(artifact_stage=PHYC1_LEGACY_STAGE_NAME, substage="full_circuit_cudaq_teacher"),
        "teacher_model": FULL_CIRCUIT_TEACHER_MODEL,
        "physical_teacher_model": FULL_CIRCUIT_TEACHER_MODEL,
        "output_dir": str(output),
        "num_qubits": int(n),
        "num_physical_qubits": int(n),
        "num_observation_slots": int(n),
        **full_circuit_depth_metadata(depth),
        "rzz_implementation": rzz_implementation,
        "rzz_gate_semantics": FULL_CIRCUIT_RZZ_GATE_SEMANTICS,
        "num_probes": int(len(probe_names)),
        "shots": int(shots),
        "mechanism_counts": mechanism_counts(records),
        "balanced_min_instances_per_mechanism": int(repetitions),
        "multicircuit_teacher_batch": True,
        "num_circuit_batches": int(repetitions),
        "sampling_contract": sampling_contract,
        "sampling": sampling_audit,
        "sampling_audit": str(output / "sampling_audit.json"),
        "sampling_progress": str(output / "sampling_progress.json"),
        "noise_application_audit": str(output / "noise_application_audit.json"),
        "non_clifford_audit": str(output / "non_clifford_audit.json"),
        "cptp_guardrail_passed": bool(static_artifacts["cptp_guardrail_passed"]),
        "cptp_guardrail_audit": str(output / "cptp_guardrail_audit.json"),
        "active_probe_manifest": str(output / "active_probe_manifest.json"),
    }
    (output / "summary.json").write_text(json.dumps(_json_safe(summary), indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(_summary_markdown(summary))
    return summary


def _build_cudaq_kernel(
    cudaq,
    config: Mapping[str, object],
    *,
    probe_name: str,
    inline_channels: dict[tuple[str, tuple[int, ...]], list[object]],
    num_qubits: int,
    circuit_depth: int,
    theta: float,
):
    kernel = cudaq.make_kernel()
    qubits = kernel.qalloc(int(num_qubits))
    schedule = _CudaqSchedule(kernel, qubits, inline_channels, rzz_implementation=_rzz_implementation(config))
    if any(_mechanism_set_contains(dict(config), mech) for mech in PREP_RESET_MECHANISM_IDS):
        for q in range(int(num_qubits)):
            schedule.reset(q)
    if probe_name in {"x_basis", "full_x"}:
        for q in range(int(num_qubits)):
            schedule.h(q)
    elif probe_name in {"y_basis", "full_y"}:
        for q in range(int(num_qubits)):
            schedule.h(q)
            schedule.s(q)
    elif probe_name == "alternating_x":
        for q in range(0, int(num_qubits), 2):
            schedule.h(q)
    elif probe_name == "echo":
        for q in range(int(num_qubits)):
            schedule.x(q)
    _apply_rzz_tomography_preparation(schedule, str(probe_name), int(num_qubits))
    rx_qubits = set(_profile_rx_qubits(int(num_qubits)))
    ry_qubits = set(_profile_ry_qubits(int(num_qubits)))
    rz_qubits = set(_profile_rz_qubits(int(num_qubits)))
    if any(_mechanism_set_contains(dict(config), mech) for mech in ("M13", "M14", "M20")):
        mechanism_params = config.get("mechanisms", {})
        m13_params = (
            dict(mechanism_params.get("M13", {}))
            if isinstance(mechanism_params, dict) and isinstance(mechanism_params.get("M13", {}), dict)
            else {}
        )
        if _mechanism_set_contains(dict(config), "M13"):
            axis = str(m13_params.get("axis", "rx")).lower()
            if axis == "ry":
                ry_qubits.update(_drift_targets(int(num_qubits)))
            elif axis == "rz":
                rz_qubits.update(_drift_targets(int(num_qubits)))
            else:
                rx_qubits.update(_drift_targets(int(num_qubits)))
        m14_params = (
            dict(mechanism_params.get("M14", {}))
            if isinstance(mechanism_params, dict) and isinstance(mechanism_params.get("M14", {}), dict)
            else {}
        )
        if _mechanism_set_contains(dict(config), "M14"):
            axis = str(m14_params.get("axis", m14_params.get("instruction", "rx"))).lower()
            target = _single_targets(int(num_qubits))["M14"]
            if axis == "ry":
                ry_qubits.add(target)
            elif axis == "rz":
                rz_qubits.add(target)
            else:
                rx_qubits.add(target)
        if _mechanism_set_contains(dict(config), "M20"):
            ry_qubits.add(_single_targets(int(num_qubits))["M20"])
    for _layer_idx in range(int(circuit_depth)):
        for q in range(int(num_qubits)):
            schedule.id(q)
        for q in sorted(rx_qubits):
            schedule.rx(0.13 + 0.01 * (q % 3), q)
        for q in sorted(ry_qubits):
            schedule.ry(0.11 + 0.01 * (q % 3), q)
        for q in sorted(rz_qubits):
            schedule.rz(0.09 + 0.01 * (q % 2), q)
        if _is_rzz_tomography_probe(probe_name):
            _apply_rzz_tomography_block(schedule, str(probe_name), int(num_qubits), float(theta))
        elif _is_rzz_echo_probe(probe_name):
            _apply_rzz_echo_block(schedule, str(probe_name), int(num_qubits), float(theta))
        elif _is_rzz_minimal_sign_probe(probe_name):
            _apply_rzz_minimal_sign_block(schedule, str(probe_name), int(num_qubits), float(theta))
        else:
            _apply_rzz_pauli_frame(schedule, str(probe_name), int(num_qubits))
            for _depth_step in range(_probe_rzz_depth(str(probe_name))):
                for left in range(int(num_qubits) - 1):
                    schedule.rzz(float(theta), left, left + 1)
            _apply_rzz_pauli_frame(schedule, str(probe_name), int(num_qubits))
    if probe_name == "echo":
        for q in range(int(num_qubits)):
            schedule.x(q)
    _apply_measurement_basis_rotations(schedule, str(probe_name), int(num_qubits))
    schedule.measure(range(int(num_qubits)), range(int(num_qubits)))
    return kernel


class _CudaqSchedule:
    def __init__(
        self,
        kernel,
        qubits,
        inline_channels: dict[tuple[str, tuple[int, ...]], list[object]],
        *,
        rzz_implementation: str = "cx_rz_cx",
    ) -> None:
        self.kernel = kernel
        self.qubits = qubits
        self.inline_channels = inline_channels
        self.rzz_implementation = _rzz_implementation({"full_circuit_cudaq_rzz_implementation": rzz_implementation})

    def h(self, qubit: int) -> None:
        self.kernel.h(self.qubits[int(qubit)])
        self._noise("h", (int(qubit),))

    def s(self, qubit: int) -> None:
        self.kernel.s(self.qubits[int(qubit)])
        self._noise("s", (int(qubit),))

    def sdg(self, qubit: int) -> None:
        self.kernel.sdg(self.qubits[int(qubit)])
        self._noise("sdg", (int(qubit),))

    def x(self, qubit: int) -> None:
        self.kernel.x(self.qubits[int(qubit)])
        self._noise("x", (int(qubit),))

    def y(self, qubit: int) -> None:
        self.kernel.y(self.qubits[int(qubit)])
        self._noise("y", (int(qubit),))

    def id(self, qubit: int) -> None:
        self._noise("id", (int(qubit),))

    def reset(self, qubit: int) -> None:
        self.kernel.reset(self.qubits[int(qubit)])
        self._noise("reset", (int(qubit),))

    def rx(self, angle: float, qubit: int) -> None:
        self.kernel.rx(float(angle), self.qubits[int(qubit)])
        self._noise("rx", (int(qubit),))

    def ry(self, angle: float, qubit: int) -> None:
        self.kernel.ry(float(angle), self.qubits[int(qubit)])
        self._noise("ry", (int(qubit),))

    def rz(self, angle: float, qubit: int) -> None:
        self.kernel.rz(float(angle), self.qubits[int(qubit)])
        self._noise("rz", (int(qubit),))

    def rzz(self, angle: float, left: int, right: int) -> None:
        if self.rzz_implementation == "cx_rz_cx":
            self.kernel.cx(self.qubits[int(left)], self.qubits[int(right)])
            self.kernel.rz(float(angle), self.qubits[int(right)])
            self.kernel.cx(self.qubits[int(left)], self.qubits[int(right)])
        elif self.rzz_implementation == "exp_pauli":
            self.kernel.exp_pauli(-0.5 * float(angle), "ZZ", self.qubits[int(left)], self.qubits[int(right)])
        else:  # pragma: no cover - guarded by _rzz_implementation.
            raise ValueError(f"unsupported RZZ implementation {self.rzz_implementation!r}")
        self._noise("rzz", (int(left), int(right)))

    def measure(self, qubits, _clbits) -> None:
        indices = [int(q) for q in qubits]
        if indices == list(range(len(indices))):
            self.kernel.mz(self.qubits)
            return
        for q in indices:
            self.kernel.mz(self.qubits[q])

    def _noise(self, operation: str, qubits: tuple[int, ...]) -> None:
        for channel in self.inline_channels.get((str(operation), tuple(int(q) for q in qubits)), []):
            self.kernel.apply_noise(channel, *[self.qubits[int(q)] for q in qubits])


def _build_full_circuit_oracle_mechanisms(config: dict[str, object]) -> tuple[list[MechanismSpec], int, str]:
    default_count = max(1, _balanced_repetitions(config))
    instance_counts = _mechanism_instance_counts(config)
    repetitions = max(default_count, max(instance_counts.values())) if instance_counts else default_count
    local_cfg = dict(config)
    local_cfg["balanced_min_instances_per_mechanism"] = int(repetitions)
    local_cfg["multicircuit_teacher_batch"] = True
    mechanisms = _build_balanced_oracle_mechanisms(local_cfg)
    if not instance_counts:
        return mechanisms, int(repetitions), "balanced"
    seen: dict[str, int] = {}
    filtered: list[MechanismSpec] = []
    for spec in mechanisms:
        count = seen.get(spec.mechanism_id, 0)
        target = int(instance_counts.get(spec.mechanism_id, default_count))
        if count >= target:
            continue
        seen[spec.mechanism_id] = count + 1
        filtered.append(spec)
    return filtered, int(repetitions), "weighted"


def _mechanism_instance_counts(config: Mapping[str, object]) -> dict[str, int]:
    raw = config.get("mechanism_instance_counts", {})
    if not isinstance(raw, dict):
        return {}
    counts: dict[str, int] = {}
    for key, value in raw.items():
        count = int(value)
        if count > 0:
            counts[str(key)] = count
    return counts


def _mechanism_channels_by_location(
    cudaq,
    mechanisms: list[MechanismSpec],
    *,
    mode: str,
    rzz_implementation: str = "cx_rz_cx",
) -> tuple[dict[tuple[str, tuple[int, ...]], list[object]], object, bool]:
    inline: dict[tuple[str, tuple[int, ...]], list[object]] = {}
    noise_model = cudaq.NoiseModel()
    has_noise_model_channels = False
    hybrid = str(mode).lower() in {"hybrid", "hybrid_noise_model", "noise_model"}
    excluded = set(_noise_model_excluded_operations(rzz_implementation))
    for spec in mechanisms:
        if spec.mechanism_id in READOUT_MECHANISM_IDS:
            continue
        instruction = str(spec.instruction or "id").lower()
        channel = _cudaq_channel_from_mechanism(cudaq, spec)
        if channel is None:
            continue
        if hybrid and instruction in NOISE_MODEL_OPERATIONS and instruction not in excluded:
            noise_model.add_channel(instruction, [int(q) for q in spec.qubits], channel)
            has_noise_model_channels = True
        else:
            inline.setdefault((instruction, tuple(int(q) for q in spec.qubits)), []).append(channel)
    return inline, noise_model, has_noise_model_channels


def _cudaq_channel_from_mechanism(cudaq, spec: MechanismSpec):
    channel = mechanism_channel(spec)
    kind = str(channel["kind"])
    if kind == "readout":
        return None
    if kind == "unitary":
        matrices = [np.asarray(channel["unitary"], dtype=np.complex128)]
    elif kind == "kraus":
        matrices = [np.asarray(item, dtype=np.complex128) for item in channel["kraus"]]  # type: ignore[index]
    else:
        raise ValueError(f"unsupported mechanism channel kind {kind!r}")
    operators = [cudaq.KrausOperator(np.ascontiguousarray(matrix, dtype=np.complex128)) for matrix in matrices]
    return cudaq.KrausChannel(operators)


def _apply_readout_mechanisms(rows: np.ndarray, mechanisms: list[MechanismSpec], *, rng: np.random.Generator) -> None:
    for spec in mechanisms:
        if spec.mechanism_id not in READOUT_MECHANISM_IDS:
            continue
        if not spec.qubits:
            continue
        q = int(spec.qubits[0])
        if q < 0 or q >= rows.shape[1]:
            continue
        channel = mechanism_channel(spec)
        matrix = np.asarray(channel.get("matrix", readout_bias_matrix(p0_to_1=0.0, p1_to_0=0.0)), dtype=np.float64)
        bits = rows[:, q].copy()
        random = rng.random(rows.shape[0])
        flip_up = (bits == 0) & (random < float(matrix[0, 1]))
        flip_down = (bits == 1) & (random < float(matrix[1, 0]))
        rows[flip_up, q] = 1
        rows[flip_down, q] = 0


def _write_static_artifacts(
    output: Path,
    *,
    cfg: dict[str, object],
    mechanisms: list[MechanismSpec],
    records: list[dict[str, object]],
    probe_names: list[str],
    num_qubits: int,
    circuit_depth: int,
    target_audit: dict[str, object],
) -> dict[str, object]:
    (output / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2, sort_keys=True) + "\n")
    (output / "teacher_config.json").write_text(json.dumps(_json_safe(cfg), indent=2, sort_keys=True) + "\n")
    probe_manifest = build_probe_basis_manifest(probe_names, num_qubits=num_qubits, circuit_depth=circuit_depth)
    probe_manifest["teacher_model"] = FULL_CIRCUIT_TEACHER_MODEL
    probe_manifest["num_physical_qubits"] = int(num_qubits)
    probe_manifest["num_observation_slots"] = int(num_qubits)
    probe_manifest.update(full_circuit_depth_metadata(circuit_depth))
    probe_manifest["rzz_implementation"] = _rzz_implementation(cfg)
    probe_manifest["rzz_gate_semantics"] = FULL_CIRCUIT_RZZ_GATE_SEMANTICS
    (output / "active_probe_manifest.json").write_text(json.dumps(_json_safe(probe_manifest), indent=2, sort_keys=True) + "\n")
    noise_audit = build_noise_application_audit(mechanisms, probe_names=probe_names, config=cfg)
    noise_audit["teacher_model"] = FULL_CIRCUIT_TEACHER_MODEL
    noise_audit.update(full_circuit_depth_metadata(circuit_depth))
    noise_audit["cudaq_target"] = target_audit.get("cudaq_target")
    noise_audit["rzz_implementation"] = _rzz_implementation(cfg)
    noise_audit["rzz_gate_semantics"] = FULL_CIRCUIT_RZZ_GATE_SEMANTICS
    noise_audit["noise_model_excluded_operations"] = _noise_model_excluded_operations(_rzz_implementation(cfg))
    noise_audit["mechanism_application_convention"] = FULL_CIRCUIT_MECHANISM_APPLICATION_CONVENTION
    noise_audit["readout_application_convention"] = READOUT_APPLICATION_CONVENTION
    (output / "noise_application_audit.json").write_text(json.dumps(_json_safe(noise_audit), indent=2, sort_keys=True) + "\n")
    non_clifford = build_non_clifford_audit(mechanisms, probe_names=probe_names, config=cfg)
    non_clifford["teacher_model"] = FULL_CIRCUIT_TEACHER_MODEL
    (output / "non_clifford_audit.json").write_text(json.dumps(_json_safe(non_clifford), indent=2, sort_keys=True) + "\n")
    cptp_guardrail = build_cptp_guardrail_audit(mechanisms)
    (output / "cptp_guardrail_audit.json").write_text(json.dumps(_json_safe(cptp_guardrail), indent=2, sort_keys=True) + "\n")
    return {"cptp_guardrail_passed": bool(cptp_guardrail["passed"])}


def _initial_progress(
    cfg: Mapping[str, object],
    *,
    output: Path,
    target_audit: dict[str, object],
    num_qubits: int,
    circuit_depth: int,
    shots: int,
    repetitions: int,
    probe_names: list[str],
    shot_batch_size: int,
) -> dict[str, object]:
    return {
        "schema": "scope_static_full_circuit_cudaq_sampling_progress_v1",
        "teacher_model": FULL_CIRCUIT_TEACHER_MODEL,
        "physical_teacher_model": FULL_CIRCUIT_TEACHER_MODEL,
        "output_dir": str(output),
        "cudaq_target": target_audit.get("cudaq_target"),
        "cudaq_target_description": target_audit.get("cudaq_target_description"),
        "cudaq_target_options": target_audit.get("cudaq_target_options"),
        "require_gpu": bool(target_audit.get("require_gpu", True)),
        "cpu_fallback_allowed": bool(target_audit.get("cpu_fallback_allowed", False)),
        "num_qubits": int(num_qubits),
        "num_physical_qubits": int(num_qubits),
        "num_observation_slots": int(num_qubits),
        **full_circuit_depth_metadata(circuit_depth),
        "rzz_implementation": _rzz_implementation(cfg),
        "rzz_gate_semantics": FULL_CIRCUIT_RZZ_GATE_SEMANTICS,
        "shots": int(shots),
        "shot_batch_size": int(shot_batch_size),
        "num_probe_circuits": int(len(probe_names)),
        "num_circuit_id_groups": int(repetitions),
        "completed_probe_circuits": 0,
        "completed_probe_circuits_this_run": 0,
        "completed_shot_chunks": 0,
        "skipped_resumed_probe_circuits": 0,
        "resumed_shot_chunks": 0,
        "resumed_shots": 0,
        "active_probe_index": None,
        "active_probe_name": None,
        "completed_shots_in_active_probe": 0,
        "completed": False,
        "noise_application_mode": str(cfg.get("full_circuit_cudaq_noise_mode", "hybrid")),
        "noise_model_excluded_operations": _noise_model_excluded_operations(_rzz_implementation(cfg)),
        "contract_note": FULL_CIRCUIT_CONTRACT_NOTE,
    }


def _write_progress(output: Path, progress: dict[str, object]) -> None:
    (output / "sampling_progress.json").write_text(json.dumps(_json_safe(progress), indent=2, sort_keys=True) + "\n")


def _probe_checkpoint_path(checkpoint_dir: Path, probe_index: int) -> Path:
    return checkpoint_dir / f"probe_{int(probe_index):06d}.npz"


def _chunk_checkpoint_path(checkpoint_dir: Path, probe_index: int, chunk_index: int) -> Path:
    return checkpoint_dir / f"probe_{int(probe_index):06d}_chunk_{int(chunk_index):06d}.npz"


def _write_chunk_checkpoint(
    checkpoint_dir: Path,
    *,
    probe_index: int,
    chunk_index: int,
    start: int,
    end: int,
    rows: np.ndarray,
    metadata: dict[str, object],
) -> Path:
    path = _chunk_checkpoint_path(checkpoint_dir, probe_index, chunk_index)
    tmp = path.with_name(path.name + ".tmp.npz")
    np.savez(
        tmp,
        observations=np.asarray(rows, dtype=np.uint8),
        start=np.asarray([int(start)], dtype=np.int64),
        end=np.asarray([int(end)], dtype=np.int64),
        metadata=np.asarray(json.dumps(_json_safe(metadata), sort_keys=True)),
    )
    tmp.replace(path)
    return path


def _load_probe_checkpoint_metadata(path: Path, *, probe_index: int, shots: int, num_qubits: int) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        with np.load(path, allow_pickle=False) as data:
            rows = data["observations"]
            if rows.shape != (int(shots), int(num_qubits)):
                return None
            metadata = json.loads(str(data["metadata"].item())) if "metadata" in data else {}
    except Exception:
        return None
    if int(metadata.get("probe_index", probe_index)) != int(probe_index):
        return None
    return {
        "circuit_id": int(metadata.get("circuit_id", 0)),
        "probe_index": int(probe_index),
        "probe_name": str(metadata.get("probe_name", f"probe_{probe_index}")),
        "unique_outcomes_max": int(metadata.get("unique_outcomes_max", 0)),
        "chunk_count": int(metadata.get("chunk_count", 1)),
        "checkpoint_path": str(path),
    }


def _contiguous_chunk_paths(
    checkpoint_dir: Path,
    *,
    probe_index: int,
    shots: int,
    num_qubits: int,
) -> tuple[list[Path], int]:
    paths = sorted(checkpoint_dir.glob(f"probe_{int(probe_index):06d}_chunk_*.npz"))
    contiguous: list[Path] = []
    expected_start = 0
    for path in paths:
        try:
            with np.load(path, allow_pickle=False) as data:
                start = int(data["start"][0])
                end = int(data["end"][0])
                rows = data["observations"]
        except Exception:
            continue
        if start != expected_start or end <= start or rows.shape != (end - start, int(num_qubits)):
            break
        contiguous.append(path)
        expected_start = end
        if expected_start >= int(shots):
            break
    return contiguous, min(expected_start, int(shots))


def _consolidate_probe_checkpoint(
    chunk_paths: list[Path],
    path: Path,
    metadata: dict[str, object],
    *,
    shots: int,
    num_qubits: int,
) -> dict[str, object]:
    rows = []
    for chunk in chunk_paths:
        with np.load(chunk, allow_pickle=False) as data:
            rows.append(np.asarray(data["observations"], dtype=np.uint8))
    if rows:
        observations = np.concatenate(rows, axis=0)
    else:
        observations = np.zeros((0, int(num_qubits)), dtype=np.uint8)
    if observations.shape != (int(shots), int(num_qubits)):
        raise RuntimeError(f"probe checkpoint {path} has shape {observations.shape}, expected {(shots, num_qubits)}")
    tmp = path.with_name(path.name + ".tmp.npz")
    np.savez(
        tmp,
        observations=observations,
        metadata=np.asarray(json.dumps(_json_safe(metadata), sort_keys=True)),
    )
    tmp.replace(path)
    for chunk in chunk_paths:
        try:
            chunk.unlink()
        except FileNotFoundError:
            pass
    return dict(metadata)


def _assemble_observations(checkpoint_dir: Path, *, num_probes: int, shots: int, num_qubits: int) -> np.ndarray:
    observations = np.empty((int(num_probes), int(shots), int(num_qubits)), dtype=np.uint8)
    missing = []
    for probe_index in range(int(num_probes)):
        path = _probe_checkpoint_path(checkpoint_dir, probe_index)
        if not path.exists():
            missing.append(probe_index)
            continue
        with np.load(path, allow_pickle=False) as data:
            rows = np.asarray(data["observations"], dtype=np.uint8)
        if rows.shape != (int(shots), int(num_qubits)):
            raise RuntimeError(f"probe checkpoint {path} has shape {rows.shape}, expected {(shots, num_qubits)}")
        observations[probe_index] = rows
    if missing:
        raise RuntimeError(f"missing probe checkpoints: {missing[:10]}")
    return observations


def _mechanism_records(mechanisms: list[MechanismSpec]) -> list[dict[str, object]]:
    return [
        {
            "location_id": int(idx),
            **spec.audit_dict(),
            "oracle_label": spec.mechanism_id,
            "oracle_label_evaluator_only": True,
        }
        for idx, spec in enumerate(mechanisms)
    ]


def _shot_batch_size(config: Mapping[str, object], *, shots: int, num_qubits: int, circuit_depth: int) -> int:
    raw = config.get("full_circuit_cudaq_shot_batch_size", config.get("cudaq_shot_batch_size"))
    if raw is not None:
        return min(int(shots), max(1, int(raw)))
    if int(shots) <= 1024:
        return int(shots)
    if int(num_qubits) >= 20 or int(circuit_depth) >= 10:
        return min(int(shots), 512)
    return min(int(shots), 2048)


def _rzz_implementation(config: Mapping[str, object]) -> str:
    raw = str(config.get("full_circuit_cudaq_rzz_implementation", "cx_rz_cx") or "cx_rz_cx").strip().lower()
    aliases = {
        "cx-rz-cx": "cx_rz_cx",
        "cnot_rz_cnot": "cx_rz_cx",
        "decomposed": "cx_rz_cx",
        "native": "cx_rz_cx",
        "exp-pauli": "exp_pauli",
        "exppauli": "exp_pauli",
    }
    value = aliases.get(raw, raw)
    if value not in {"cx_rz_cx", "exp_pauli"}:
        raise ValueError("full_circuit_cudaq_rzz_implementation must be 'cx_rz_cx' or 'exp_pauli'")
    return value


def _noise_model_excluded_operations(rzz_implementation: str) -> list[str]:
    if str(rzz_implementation) == "cx_rz_cx":
        return ["cx", "rz"]
    return []


def _chunk_seed(*, seed: int, probe_index: int, start: int) -> int:
    return int((int(seed) + 1_000_003 * int(probe_index) + 9_176 * int(start)) % (2**31 - 1))


def _set_cudaq_seed(cudaq, seed: int) -> None:
    if hasattr(cudaq, "set_random_seed"):
        cudaq.set_random_seed(int(seed))


def _configure_cudaq_target(cudaq, config: Mapping[str, object]) -> dict[str, object]:
    target = str(config.get("cudaq_target", "") or "").strip()
    options = str(config.get("cudaq_target_options", "") or "").strip()
    require_gpu = bool(config.get("require_gpu", True))
    if require_gpu and not target:
        target = "nvidia"
        if not options:
            options = "fp32"
    if target:
        try:
            if options:
                cudaq.set_target(target, option=options)
            else:
                cudaq.set_target(target)
        except TypeError:
            if options:
                cudaq.set_target(target, options)
            else:
                cudaq.set_target(target)
    target_name = None
    target_description = None
    try:
        current = cudaq.get_target()
        target_name = str(current.name if hasattr(current, "name") else current)
        target_description = str(current)
    except Exception:
        target_name = target or None
    if require_gpu and not _cudaq_target_looks_gpu(target_name, target_description):
        raise RuntimeError(
            "full-circuit PHYC1 requires a GPU CUDA-Q target; refusing CPU fallback "
            f"(target={target_name!r}, options={options!r})"
        )
    return {
        "cudaq_target": target_name,
        "cudaq_target_description": target_description,
        "cudaq_target_options": options,
        "require_gpu": bool(require_gpu),
        "cpu_fallback_allowed": False,
    }


def _cudaq_target_looks_gpu(target_name: object, target_description: object) -> bool:
    text = f"{target_name or ''}\n{target_description or ''}".lower()
    return any(marker in text for marker in ("nvidia", "custatevec", "cusvsim", "cutensornet", "gpu"))


def _cudaq():
    import cudaq

    return cudaq


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


def _summary_markdown(summary: dict[str, object]) -> str:
    sampling = summary.get("sampling", {})
    if not isinstance(sampling, dict):
        sampling = {}
    return "\n".join(
        [
            "# PHYS1 Full-Circuit CUDA-Q Teacher",
            "",
            f"- Output: `{summary.get('output_dir')}`",
            f"- Teacher model: `{summary.get('teacher_model')}`",
            f"- CUDA-Q target: `{sampling.get('cudaq_target')}`",
            f"- Qubits: `{summary.get('num_qubits')}`",
            f"- Configured circuit depth: `{summary.get('configured_circuit_depth')}`",
            f"- Effective circuit depth: `{summary.get('effective_circuit_depth')}`",
            f"- RZZ implementation: `{summary.get('rzz_implementation')}`",
            f"- Probes: `{summary.get('num_probes')}`",
            f"- Shots: `{summary.get('shots')}`",
            f"- Mechanisms: `{summary.get('mechanism_counts')}`",
            f"- Completed probe circuits: `{sampling.get('completed_probe_circuits')}`",
            f"- Skipped/resumed probe circuits: `{sampling.get('skipped_resumed_probe_circuits')}`",
            f"- Sampling seconds: `{float(sampling.get('sampling_wall_clock_seconds', 0.0)):.6f}`",
            f"- Total seconds: `{float(sampling.get('total_wall_clock_seconds', 0.0)):.6f}`",
            "",
        ]
    )


def _log(enabled: bool, message: str) -> None:
    if enabled:
        print(message, flush=True)
