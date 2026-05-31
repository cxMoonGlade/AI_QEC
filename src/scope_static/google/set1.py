from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Callable, Iterable

import numpy as np
import stim
import torch

from ..dem.fault_graph import FaultGraph, _mask_key
from ..dem.metrics import partition_audit, partition_comparison


DATASET_NAME = "google_72Q_surface_code_d3_d5_set1"

DECODER_ALIASES = {
    "decoder_si1000": "correlated_matching_decoder_with_si1000_prior",
    "decoder_rl": "correlated_matching_decoder_with_rl_optimized_prior",
    "matching_si1000": "correlated_matching_decoder_with_si1000_prior",
    "matching_rl": "correlated_matching_decoder_with_rl_optimized_prior",
    "harmony_si1000": "harmony_decoder_with_si1000_prior",
    "harmony_rl": "harmony_decoder_with_rl_optimized_prior",
}

CLAIM_BOUNDARY = {
    "schedule_geometric": (
        "schedule_geometric is an audited schedule-derived preprocessing proxy. "
        "It is not a full hardware automorphism solver, not full SCOPE-Twin, "
        "and not CPTP/GKSL learning. It only tests whether schedule-derived "
        "coloring gives a better fixed quotient/orbit prior than the current "
        "DEM-mask geometry heuristic."
    ),
    "orbit_target": (
        "S1.6 still induces orbits over effective DEM fault columns, not true "
        "hardware/schedule fault locations."
    ),
}


@dataclass(frozen=True)
class GoogleSet1Leaf:
    root: Path
    sample_id: str
    patch_id: str
    basis: str
    rounds_label: str

    @property
    def path(self) -> Path:
        return self.root / self.sample_id / self.patch_id / self.basis / self.rounds_label

    @property
    def sample_index(self) -> int:
        match = re.search(r"(\d+)$", self.sample_id)
        return int(match.group(1)) if match else -1

    @property
    def rounds(self) -> int:
        match = re.search(r"(\d+)$", self.rounds_label)
        return int(match.group(1)) if match else -1

    @property
    def metadata_path(self) -> Path:
        return self.path / "metadata.json"

    @property
    def circuit_ideal_path(self) -> Path:
        return self.path / "circuit_ideal.stim"

    @property
    def circuit_noisy_si1000_path(self) -> Path:
        return self.path / "circuit_noisy_si1000.stim"

    @property
    def detection_events_path(self) -> Path:
        return self.path / "detection_events.b8"

    @property
    def obs_flips_actual_path(self) -> Path:
        return self.path / "obs_flips_actual.b8"

    @property
    def measurements_path(self) -> Path:
        return self.path / "measurements.b8"

    @property
    def sweep_bits_path(self) -> Path:
        return self.path / "sweep_bits.b8"

    def decoder_dir(self, dem_source: str) -> Path:
        decoder_name = DECODER_ALIASES.get(dem_source, dem_source)
        return self.path / "decoding_results" / decoder_name

    def decoder_dem_path(self, dem_source: str) -> Path:
        return self.decoder_dir(dem_source) / "error_model.dem"

    def decoder_predictions_path(self, dem_source: str) -> Path:
        return self.decoder_dir(dem_source) / "obs_flips_predicted.b8"


@dataclass(frozen=True)
class GoogleDemData:
    raw_masks: torch.Tensor
    raw_probabilities: torch.Tensor
    num_detectors: int
    num_observables: int
    detector_coordinates: torch.Tensor | None
    dem_source: str
    source_path: Path


@dataclass(frozen=True)
class GoogleScheduleContext:
    """Minimal Stage-1 proxy for c = (H_sched, u, kappa, tau)."""

    h_sched: dict[str, object]
    u: dict[str, object]
    kappa: dict[str, object]
    tau: dict[str, object]
    coverage_audit: dict[str, object]
    claim_boundary: dict[str, str]

    def audit_dict(self) -> dict[str, object]:
        return {
            "H_sched": self.h_sched,
            "u": self.u,
            "kappa": self.kappa,
            "tau": self.tau,
            "H_sched_coverage_audit": self.coverage_audit,
            "claim_boundary": self.claim_boundary,
        }


def normalize_google_set1_root(path: str | Path) -> Path:
    """Accept either the outer Google Set1 path or the nested dataset path."""

    start = Path(path).expanduser()
    candidates = [start, start / DATASET_NAME]
    for candidate in candidates:
        if (candidate / "sample_00").is_dir():
            return candidate.resolve()
    checked = ", ".join(str(candidate) for candidate in candidates)
    raise ValueError(f"Google Set1 root must contain sample_00; checked {checked}")


def iter_google_set1_leaves(root: str | Path) -> list[GoogleSet1Leaf]:
    dataset_root = normalize_google_set1_root(root)
    leaves: list[GoogleSet1Leaf] = []
    for sample_dir in sorted(dataset_root.glob("sample_*")):
        if not sample_dir.is_dir():
            continue
        for patch_dir in sorted(path for path in sample_dir.iterdir() if path.is_dir()):
            for basis_dir in sorted(path for path in patch_dir.iterdir() if path.is_dir()):
                for rounds_dir in sorted(path for path in basis_dir.iterdir() if path.is_dir()):
                    if rounds_dir.name.startswith("r") and (rounds_dir / "metadata.json").is_file():
                        leaves.append(
                            GoogleSet1Leaf(
                                root=dataset_root,
                                sample_id=sample_dir.name,
                                patch_id=patch_dir.name,
                                basis=basis_dir.name,
                                rounds_label=rounds_dir.name,
                            )
                        )
    return leaves


def find_google_set1_leaf(
    root: str | Path,
    *,
    sample_id: str = "sample_00",
    patch_id: str = "d3_at_q5_5",
    basis: str = "X",
    rounds_label: str = "r13",
) -> GoogleSet1Leaf:
    dataset_root = normalize_google_set1_root(root)
    leaf = GoogleSet1Leaf(
        root=dataset_root,
        sample_id=sample_id,
        patch_id=patch_id,
        basis=basis,
        rounds_label=rounds_label,
    )
    if not leaf.path.is_dir():
        raise FileNotFoundError(f"Google Set1 leaf does not exist: {leaf.path}")
    if not leaf.metadata_path.is_file():
        raise FileNotFoundError(f"Google Set1 leaf is missing metadata.json: {leaf.metadata_path}")
    return leaf


def load_google_metadata(leaf: GoogleSet1Leaf) -> dict[str, object]:
    with leaf.metadata_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_google_circuit(leaf: GoogleSet1Leaf, *, noisy: bool = False) -> stim.Circuit:
    path = leaf.circuit_noisy_si1000_path if noisy else leaf.circuit_ideal_path
    return stim.Circuit.from_file(str(path))


def load_google_observations(leaf: GoogleSet1Leaf, *, max_shots: int | None = None) -> torch.Tensor:
    circuit = load_google_circuit(leaf)
    detectors = _read_b8_bits(leaf.detection_events_path, circuit.num_detectors)
    observables = _read_b8_bits(leaf.obs_flips_actual_path, circuit.num_observables)
    if detectors.shape[0] != observables.shape[0]:
        raise ValueError("detection_events.b8 and obs_flips_actual.b8 have different shot counts")
    observations = np.concatenate([detectors, observables], axis=1)
    if max_shots is not None:
        observations = observations[: int(max_shots)]
    return torch.from_numpy(np.ascontiguousarray(observations)).to(dtype=torch.bool)


def load_google_predicted_observables(
    leaf: GoogleSet1Leaf,
    dem_source: str,
    *,
    max_shots: int | None = None,
) -> torch.Tensor | None:
    path = leaf.decoder_predictions_path(dem_source)
    if not path.is_file():
        return None
    circuit = load_google_circuit(leaf)
    predicted = _read_b8_bits(path, circuit.num_observables)
    if max_shots is not None:
        predicted = predicted[: int(max_shots)]
    return torch.from_numpy(np.ascontiguousarray(predicted)).to(dtype=torch.bool)


def load_google_dem_data(leaf: GoogleSet1Leaf, dem_source: str = "decoder_si1000") -> GoogleDemData:
    circuit = load_google_circuit(leaf)
    if dem_source in {"noisy_si1000", "circuit_noisy_si1000"}:
        noisy_circuit = load_google_circuit(leaf, noisy=True)
        dem = noisy_circuit.detector_error_model(decompose_errors=False)
        source_path = leaf.circuit_noisy_si1000_path
    else:
        source_path = leaf.decoder_dem_path(dem_source)
        if not source_path.is_file():
            raise FileNotFoundError(f"DEM source not found: {source_path}")
        dem = stim.DetectorErrorModel.from_file(str(source_path))
    raw_masks, raw_probabilities = dem_to_raw_masks(dem)
    return GoogleDemData(
        raw_masks=raw_masks,
        raw_probabilities=raw_probabilities,
        num_detectors=int(dem.num_detectors),
        num_observables=int(dem.num_observables),
        detector_coordinates=_detector_coordinate_tensor(circuit, int(dem.num_detectors)),
        dem_source=str(dem_source),
        source_path=source_path,
    )


def dem_to_raw_masks(dem: stim.DetectorErrorModel) -> tuple[torch.Tensor, torch.Tensor]:
    masks: list[torch.Tensor] = []
    probabilities: list[float] = []
    b = int(dem.num_detectors) + int(dem.num_observables)
    for instruction in dem.flattened():
        if instruction.type != "error":
            continue
        mask = torch.zeros(b, dtype=torch.bool)
        for target in instruction.targets_copy():
            if target.is_separator():
                continue
            if target.is_relative_detector_id():
                mask[int(target.val)] ^= True
            elif target.is_logical_observable_id():
                mask[int(dem.num_detectors) + int(target.val)] ^= True
        masks.append(mask)
        args = instruction.args_copy()
        probabilities.append(float(args[0]) if args else 0.0)
    if masks:
        return torch.stack(masks, dim=1), torch.tensor(probabilities, dtype=torch.float64)
    return torch.empty((b, 0), dtype=torch.bool), torch.empty((0,), dtype=torch.float64)


def build_google_schedule_context(
    leaf: GoogleSet1Leaf,
    *,
    dem_source: str = "decoder_si1000",
    observations: torch.Tensor | None = None,
) -> GoogleScheduleContext:
    metadata = load_google_metadata(leaf)
    circuit = load_google_circuit(leaf)
    qubits = _parse_qubits(circuit, metadata)
    schedule = _parse_schedule(circuit, rounds=leaf.rounds)
    detector_defs = _detector_definitions(circuit)
    observable_defs = _observable_definitions(circuit)
    detector_bits = circuit.num_detectors
    observable_bits = circuit.num_observables
    measurement_bits = circuit.num_measurements
    sweep_bits = circuit.num_sweep_bits
    if observations is None:
        detector_observations = _read_b8_bits(leaf.detection_events_path, detector_bits)
        observable_observations = _read_b8_bits(leaf.obs_flips_actual_path, observable_bits)
        observation_shape = [int(detector_observations.shape[0]), detector_bits + observable_bits]
        detector_b8_match = int(detector_observations.shape[1]) == detector_bits
        observable_b8_match = int(observable_observations.shape[1]) == observable_bits
    else:
        observation_shape = [int(observations.shape[0]), int(observations.shape[1])]
        detector_b8_match = int(observations.shape[1]) >= detector_bits
        observable_b8_match = int(observations.shape[1]) == detector_bits + observable_bits

    patch_center = _patch_center(metadata, leaf.patch_id)
    h_sched = {
        "proxy_kind": "minimal_H_sched_proxy",
        "hardware_layout": {
            "qubits": qubits,
            "num_qubits": len(qubits),
            "num_data_qubits": sum(1 for qubit in qubits if qubit["role"] == "data"),
            "num_measure_qubits": sum(1 for qubit in qubits if qubit["role"] == "measure"),
            "patch_name": leaf.patch_id,
            "patch_center": list(patch_center) if patch_center is not None else None,
        },
        "circuit_schedule": schedule,
        "detectors": detector_defs,
        "observables": observable_defs,
        "measurement_context": {
            "measurements_b8": str(leaf.measurements_path),
            "sweep_bits_b8": str(leaf.sweep_bits_path),
            "detection_events_b8": str(leaf.detection_events_path),
            "obs_flips_actual_b8": str(leaf.obs_flips_actual_path),
            "num_measurements": int(measurement_bits),
            "num_detectors": int(detector_bits),
            "num_observables": int(observable_bits),
            "num_sweep_bits": int(sweep_bits),
            "observation_shape": observation_shape,
        },
    }
    u = {
        "metadata": metadata,
        "sample_id": leaf.sample_id,
        "sample_index": leaf.sample_index,
        "patch_id": leaf.patch_id,
        "basis": leaf.basis,
        "rounds": leaf.rounds,
        "DEM_source": dem_source,
        "decoder_pathway": DECODER_ALIASES.get(dem_source, dem_source),
        "sample_order_proxy": leaf.sample_index,
    }
    kappa = {
        "distance": int(metadata.get("distance", _distance_from_patch(leaf.patch_id) or -1)),
        "basis": leaf.basis,
        "patch": leaf.patch_id,
        "rounds": leaf.rounds,
        "detector_count": int(detector_bits),
        "observable_count": int(observable_bits),
        "circuit_family": "google_72Q_surface_code_d3_d5_set1",
    }
    tau = {
        "sample_id": leaf.sample_id,
        "sample_order_proxy": leaf.sample_index,
        "sequential_sample_time_proxy": leaf.sample_index,
    }
    coverage = {
        "num_qubits_parsed": len(qubits),
        "num_data_qubits": h_sched["hardware_layout"]["num_data_qubits"],
        "num_measure_qubits": h_sched["hardware_layout"]["num_measure_qubits"],
        "num_TICK_layers": int(schedule["num_tick_layers"]),
        "gate_instances_by_type": schedule["gate_instances_by_type"],
        "num_measurement_operations": int(schedule["num_measurement_operations"]),
        "num_reset_operations": int(schedule["num_reset_operations"]),
        "num_detectors_parsed": len(detector_defs),
        "num_logical_observables_parsed": len(observable_defs),
        "detector_coordinate_coverage": float(
            sum(1 for detector in detector_defs if detector["coords"]) / detector_bits
        )
        if detector_bits
        else 1.0,
        "observable_definition_coverage": float(len(observable_defs) / observable_bits) if observable_bits else 1.0,
        "detector_count_matches_detection_events_b8_bits_per_shot": bool(detector_b8_match),
        "observable_count_matches_obs_flips_actual_b8_bits_per_shot": bool(observable_b8_match),
    }
    return GoogleScheduleContext(
        h_sched=h_sched,
        u=u,
        kappa=kappa,
        tau=tau,
        coverage_audit=coverage,
        claim_boundary=CLAIM_BOUNDARY,
    )


def provenance_audit(
    graph: FaultGraph,
    schedule_context: GoogleScheduleContext | None = None,
    *,
    available_override: str | None = None,
    provenance_source_override: str | None = None,
) -> dict[str, object]:
    has_detector_coords = graph.detector_coordinates is not None
    support_nonempty = [len(support) > 0 for support in graph.supports_by_fault]
    if available_override is not None:
        if available_override not in {"false", "partial", "full"}:
            raise ValueError("available_override must be false, partial, or full")
        available = available_override
        source = provenance_source_override or (
            "circuit annotations" if available_override == "full" else "inferred detector support"
        )
    elif schedule_context is not None and has_detector_coords and all(support_nonempty):
        available = "partial"
        source = "inferred detector support"
    else:
        available = "false"
        source = "dem mask only"
    return {
        "dem_fault_to_schedule_provenance": {
            "available": available,
            "provenance_source": source,
            "orbits_over": "effective DEM fault columns",
            "true_hardware_schedule_location_orbits": False,
            "num_effective_faults": graph.M,
            "num_faults_with_any_support": sum(1 for value in support_nonempty if value),
            "per_effective_fault": [
                {
                    "fault": int(fault),
                    "available": available,
                    "provenance_source": source,
                    "support_size": len(support),
                }
                for fault, support in enumerate(graph.supports_by_fault)
            ],
        }
    }


def build_google_fault_graph(
    leaf: GoogleSet1Leaf,
    *,
    dem_source: str = "decoder_si1000",
    orbit_mode: str = "fault_graph_heuristic",
    residual_rank: int = 0,
    schedule_context: GoogleScheduleContext | None = None,
    dem_data: GoogleDemData | None = None,
) -> tuple[FaultGraph, dict[str, object]]:
    if orbit_mode not in {"fault_graph_heuristic", "schedule_geometric", "local"}:
        raise ValueError("orbit_mode must be fault_graph_heuristic, schedule_geometric, or local")
    dem_data = dem_data if dem_data is not None else load_google_dem_data(leaf, dem_source)
    schedule_audit: dict[str, object] | None = None
    if orbit_mode == "fault_graph_heuristic":
        graph = FaultGraph.from_raw_masks(
            dem_data.raw_masks,
            num_detectors=dem_data.num_detectors,
            num_observables=dem_data.num_observables,
            raw_probabilities=dem_data.raw_probabilities,
            detector_coordinates=dem_data.detector_coordinates,
            residual_rank=int(residual_rank),
            canonicalize_duplicate_masks=True,
        )
        heuristic_orbits = graph.orbit_ids
    elif orbit_mode == "local":
        temp_graph = FaultGraph.from_raw_masks(
            dem_data.raw_masks,
            num_detectors=dem_data.num_detectors,
            num_observables=dem_data.num_observables,
            raw_probabilities=dem_data.raw_probabilities,
            detector_coordinates=dem_data.detector_coordinates,
            residual_rank=0,
            canonicalize_duplicate_masks=True,
        )
        heuristic_orbits = temp_graph.orbit_ids
        orbit_ids = torch.arange(temp_graph.M, dtype=torch.long)
        graph = FaultGraph.from_raw_masks(
            dem_data.raw_masks,
            num_detectors=dem_data.num_detectors,
            num_observables=dem_data.num_observables,
            raw_probabilities=dem_data.raw_probabilities,
            detector_coordinates=dem_data.detector_coordinates,
            residual_rank=int(residual_rank),
            canonicalize_duplicate_masks=True,
            orbit_ids=orbit_ids,
        )
    else:
        temp_graph = FaultGraph.from_raw_masks(
            dem_data.raw_masks,
            num_detectors=dem_data.num_detectors,
            num_observables=dem_data.num_observables,
            raw_probabilities=dem_data.raw_probabilities,
            detector_coordinates=dem_data.detector_coordinates,
            residual_rank=0,
            canonicalize_duplicate_masks=True,
        )
        heuristic_orbits = temp_graph.orbit_ids
        if schedule_context is None:
            schedule_context = build_google_schedule_context(leaf, dem_source=dem_source)
        orbit_ids, schedule_audit = schedule_geometric_orbit_ids(temp_graph, schedule_context)
        graph = FaultGraph.from_raw_masks(
            dem_data.raw_masks,
            num_detectors=dem_data.num_detectors,
            num_observables=dem_data.num_observables,
            raw_probabilities=dem_data.raw_probabilities,
            detector_coordinates=dem_data.detector_coordinates,
            residual_rank=int(residual_rank),
            canonicalize_duplicate_masks=True,
            orbit_ids=orbit_ids,
        )
    if schedule_context is None:
        schedule_context = build_google_schedule_context(leaf, dem_source=dem_source)
    audit = {
        "preprocessing_mode": orbit_mode,
        "claim_boundary": CLAIM_BOUNDARY,
        "dem_source": dem_source,
        "dem_source_path": str(dem_data.source_path),
        "M_raw": int(dem_data.raw_masks.shape[1]),
        "M_effective": graph.M,
        "B": graph.B,
        "O": graph.O,
        "partition": partition_audit(graph.orbit_ids),
        "partition_comparison": partition_comparison(heuristic_orbits, graph.orbit_ids),
        "google_schedule_context": schedule_context.audit_dict(),
    }
    audit.update(provenance_audit(graph, schedule_context))
    if schedule_audit is not None:
        audit["schedule_symmetry_validation"] = schedule_audit
        audit["schedule_symmetry_status"] = schedule_audit["schedule_symmetry_status"]
    elif orbit_mode == "schedule_geometric":
        audit["schedule_symmetry_status"] = "invalid"
    return graph, audit


def schedule_geometric_orbit_ids(
    graph: FaultGraph,
    schedule_context: GoogleScheduleContext,
) -> tuple[torch.Tensor, dict[str, object]]:
    candidates = _candidate_transforms(schedule_context)
    reason_counts = {
        "qubit role not preserved": 0,
        "detector coordinate not preserved": 0,
        "logical observable identity not preserved": 0,
        "effective DEM fault mask not found": 0,
        "A-invariance failed": 0,
    }
    accepted: list[dict[str, object]] = []
    rejected: list[dict[str, object]] = []
    for name, transform in candidates:
        result = _validate_candidate_transform(graph, schedule_context, name, transform)
        if result["accepted"]:
            accepted.append(
                {
                    "name": name,
                    "is_identity": bool(name == "identity"),
                    "tau": result["tau"],
                    "A_invariance_checked_over": "effective DEM faults",
                }
            )
        else:
            reason = str(result["reason"])
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
            rejected.append({"name": name, "reason": reason})
    identity_ok = any(item["name"] == "identity" for item in accepted)
    if not identity_ok:
        status = "invalid"
        orbit_ids = torch.arange(graph.M, dtype=torch.long)
    else:
        nontrivial = [
            item
            for item in accepted
            if any(int(mapped) != fault for fault, mapped in enumerate(item["tau"]))
        ]
        status = "nontrivial" if nontrivial else "identity_only"
        orbit_ids = _orbits_from_permutations(graph.M, [item["tau"] for item in accepted])
    audit = {
        "candidate_generator_names": [name for name, _ in candidates],
        "num_candidates": len(candidates),
        "accepted_candidates": [item["name"] for item in accepted],
        "num_accepted_candidates": len(accepted),
        "rejected_candidates": rejected,
        "num_rejected_candidates": len(rejected),
        "rejection_reason_counts": reason_counts,
        "accepted_candidate_A_invariance": [
            {
                "name": item["name"],
                "satisfies_A_sigma_tau_invariance": True,
                "checked_over": "effective DEM faults, not raw DEM rows",
            }
            for item in accepted
        ],
        "schedule_symmetry_status": status,
    }
    return orbit_ids, audit


def _read_b8_bits(path: Path, bits_per_shot: int) -> np.ndarray:
    if bits_per_shot < 0:
        raise ValueError("bits_per_shot must be non-negative")
    return stim.read_shot_data_file(
        path=str(path),
        format="b8",
        num_measurements=int(bits_per_shot),
    ).astype(np.bool_, copy=False)


def _detector_coordinate_dict(circuit: stim.Circuit) -> dict[int, tuple[float, ...]]:
    return {
        int(index): tuple(float(value) for value in coords)
        for index, coords in circuit.get_detector_coordinates().items()
    }


def _detector_coordinate_tensor(circuit: stim.Circuit, num_detectors: int) -> torch.Tensor | None:
    coords = _detector_coordinate_dict(circuit)
    if len(coords) < int(num_detectors):
        return None
    dim = max((len(value) for value in coords.values()), default=0)
    if dim == 0:
        return None
    rows: list[list[float]] = []
    for detector in range(int(num_detectors)):
        if detector not in coords:
            return None
        row = list(coords[detector])
        row.extend([0.0] * (dim - len(row)))
        rows.append(row)
    return torch.tensor(rows, dtype=torch.float64)


def _detector_definitions(circuit: stim.Circuit) -> list[dict[str, object]]:
    detectors = []
    index = 0
    for instruction in circuit.flattened():
        if instruction.name != "DETECTOR":
            continue
        targets = []
        for group in instruction.target_groups():
            targets.extend(_gate_target_repr(target) for target in group)
        detectors.append(
            {
                "index": int(index),
                "coords": [float(value) for value in instruction.gate_args_copy()],
                "targets": targets,
            }
        )
        index += 1
    return detectors


def _parse_qubits(circuit: stim.Circuit, metadata: dict[str, object]) -> list[dict[str, object]]:
    data_coords = {_coord_key(coord): "data" for coord in metadata.get("data_qubit_coords", [])}
    measure_coords = {_coord_key(coord): "measure" for coord in metadata.get("meas_qubit_coords", [])}
    qubit_coords: dict[int, tuple[float, ...]] = {}
    for instruction in circuit.flattened():
        if instruction.name != "QUBIT_COORDS":
            continue
        args = tuple(float(arg) for arg in instruction.gate_args_copy())
        for group in instruction.target_groups():
            for target in group:
                if target.is_qubit_target:
                    qubit_coords[int(target.qubit_value)] = args
    qubits = []
    for index, coords in sorted(qubit_coords.items()):
        key = _coord_key(coords)
        role = data_coords.get(key) or measure_coords.get(key) or "other"
        boundary_role = _boundary_role(coords, metadata)
        qubits.append(
            {
                "index": int(index),
                "coords": [float(value) for value in coords],
                "role": role,
                "boundary_role": boundary_role,
            }
        )
    return qubits


def _parse_schedule(circuit: stim.Circuit, *, rounds: int) -> dict[str, object]:
    flattened = list(circuit.flattened())
    total_ticks = sum(1 for instruction in flattened if instruction.name == "TICK")
    tick = 0
    gates_by_type: Counter[str] = Counter()
    gates_by_name: Counter[str] = Counter()
    measurement_ops = 0
    reset_ops = 0
    sweep_conditioned_ops = 0
    gate_instances = []
    for instruction in flattened:
        name = instruction.name
        if name == "TICK":
            tick += 1
            continue
        if name in {"QUBIT_COORDS", "DETECTOR", "OBSERVABLE_INCLUDE"}:
            continue
        groups = instruction.target_groups()
        category = _gate_category(name, groups)
        count = max(1, len(groups))
        gates_by_type[category] += count
        gates_by_name[name] += count
        if category == "measurement":
            measurement_ops += int(instruction.num_measurements)
        if category == "reset" or name.startswith("MR"):
            reset_ops += count
        if _has_sweep_target(groups):
            sweep_conditioned_ops += count
        gate_instances.append(
            {
                "name": name,
                "type": category,
                "tick": int(tick),
                "layer_index": int(tick),
                "round_proxy": _round_proxy(tick, max(1, rounds), max(1, total_ticks)),
                "num_target_groups": int(count),
                "sweep_conditioned": bool(_has_sweep_target(groups)),
            }
        )
    return {
        "gate_instances": gate_instances,
        "num_gate_instances": len(gate_instances),
        "gate_instances_by_type": {key: int(gates_by_type[key]) for key in sorted(gates_by_type)},
        "gate_instances_by_name": {key: int(gates_by_name[key]) for key in sorted(gates_by_name)},
        "num_tick_layers": int(tick),
        "num_measurement_operations": int(measurement_ops),
        "num_reset_operations": int(reset_ops),
        "num_sweep_conditioned_operations": int(sweep_conditioned_ops),
    }


def _observable_definitions(circuit: stim.Circuit) -> list[dict[str, object]]:
    observables = []
    for instruction in circuit.flattened():
        if instruction.name != "OBSERVABLE_INCLUDE":
            continue
        args = instruction.gate_args_copy()
        observable = int(args[0]) if args else 0
        targets = []
        for group in instruction.target_groups():
            targets.extend(_gate_target_repr(target) for target in group)
        observables.append({"index": observable, "targets": targets})
    by_index: dict[int, list[str]] = {}
    for item in observables:
        by_index.setdefault(int(item["index"]), []).extend(str(target) for target in item["targets"])
    return [{"index": key, "targets": value} for key, value in sorted(by_index.items())]


def _gate_category(name: str, groups: list[list[stim.GateTarget]]) -> str:
    if name.startswith("M"):
        return "measurement"
    if name.startswith("R"):
        return "reset"
    if _has_sweep_target(groups):
        return "sweep_conditioned"
    max_qubits = 0
    for group in groups:
        qubit_count = sum(1 for target in group if target.is_qubit_target)
        max_qubits = max(max_qubits, qubit_count)
    if max_qubits >= 2:
        return "two_qubit"
    if max_qubits == 1:
        return "one_qubit"
    return "other"


def _has_sweep_target(groups: list[list[stim.GateTarget]]) -> bool:
    return any(target.is_sweep_bit_target for group in groups for target in group)


def _gate_target_repr(target: stim.GateTarget) -> str:
    if target.is_qubit_target:
        return f"q{int(target.qubit_value)}"
    if target.is_sweep_bit_target:
        return f"sweep[{int(target.value)}]"
    if target.is_measurement_record_target:
        return f"rec[{int(target.value)}]"
    return repr(target)


def _round_proxy(tick: int, rounds: int, tick_count_proxy: int) -> int:
    return int(min(rounds - 1, max(0, int(tick * rounds / max(1, tick_count_proxy)))))


def _candidate_transforms(
    schedule_context: GoogleScheduleContext,
) -> list[tuple[str, Callable[[float, float], tuple[float, float]]]]:
    center = schedule_context.h_sched["hardware_layout"].get("patch_center")
    if center is None:
        cx = cy = 0.0
    else:
        cx, cy = float(center[0]), float(center[1])
    return [
        ("identity", lambda x, y: (x, y)),
        ("reflect_x", lambda x, y: (2 * cx - x, y)),
        ("reflect_y", lambda x, y: (x, 2 * cy - y)),
        ("rotate_180", lambda x, y: (2 * cx - x, 2 * cy - y)),
        ("rotate_90", lambda x, y: (cx - (y - cy), cy + (x - cx))),
        ("rotate_270", lambda x, y: (cx + (y - cy), cy - (x - cx))),
        ("transpose", lambda x, y: (cx + (y - cy), cy + (x - cx))),
        ("anti_transpose", lambda x, y: (cx - (y - cy), cy - (x - cx))),
    ]


def _validate_candidate_transform(
    graph: FaultGraph,
    schedule_context: GoogleScheduleContext,
    name: str,
    transform: Callable[[float, float], tuple[float, float]],
) -> dict[str, object]:
    if not _qubit_roles_preserved(schedule_context, transform):
        return {"accepted": False, "reason": "qubit role not preserved"}
    detector_perm = _detector_permutation(graph, transform)
    if detector_perm is None:
        return {"accepted": False, "reason": "detector coordinate not preserved"}
    if graph.num_observables > 1 and name != "identity":
        return {"accepted": False, "reason": "logical observable identity not preserved"}
    tau = _fault_permutation(graph, detector_perm)
    if tau is None:
        return {"accepted": False, "reason": "effective DEM fault mask not found"}
    if not _check_A_invariance(graph, detector_perm, tau):
        return {"accepted": False, "reason": "A-invariance failed"}
    return {"accepted": True, "tau": tau}


def _qubit_roles_preserved(
    schedule_context: GoogleScheduleContext,
    transform: Callable[[float, float], tuple[float, float]],
) -> bool:
    qubits = schedule_context.h_sched["hardware_layout"].get("qubits", [])
    by_role: dict[str, set[tuple[float, ...]]] = {}
    for qubit in qubits:
        coords = tuple(float(value) for value in qubit.get("coords", []))
        role = str(qubit.get("role", "other"))
        by_role.setdefault(role, set()).add(_coord_key(coords))
    for qubit in qubits:
        coords = tuple(float(value) for value in qubit.get("coords", []))
        role = str(qubit.get("role", "other"))
        transformed = _transform_coord(coords, transform)
        if _coord_key(transformed) not in by_role.get(role, set()):
            return False
    return True


def _detector_permutation(
    graph: FaultGraph,
    transform: Callable[[float, float], tuple[float, float]],
) -> list[int] | None:
    if graph.detector_coordinates is None:
        return None
    coords = graph.detector_coordinates.cpu().tolist()
    coord_to_detector: dict[tuple[float, ...], int] = {}
    for detector, coord in enumerate(coords):
        key = _coord_key(coord)
        if key in coord_to_detector:
            return None
        coord_to_detector[key] = detector
    permutation = []
    seen: set[int] = set()
    for coord in coords:
        key = _coord_key(_transform_coord(tuple(float(value) for value in coord), transform))
        if key not in coord_to_detector:
            return None
        mapped = coord_to_detector[key]
        if mapped in seen:
            return None
        seen.add(mapped)
        permutation.append(mapped)
    return permutation


def _fault_permutation(graph: FaultGraph, detector_perm: list[int]) -> list[int] | None:
    a = graph.A
    key_to_fault = {_mask_key(a[:, col]): col for col in range(graph.M)}
    tau: list[int] = []
    seen: set[int] = set()
    for fault in range(graph.M):
        transformed = _transform_mask(a[:, fault], graph.num_detectors, graph.num_observables, detector_perm)
        key = _mask_key(transformed)
        if key not in key_to_fault:
            return None
        mapped = int(key_to_fault[key])
        if mapped in seen:
            return None
        seen.add(mapped)
        tau.append(mapped)
    return tau


def _check_A_invariance(graph: FaultGraph, detector_perm: list[int], tau: list[int]) -> bool:
    a = graph.A
    for fault, mapped_fault in enumerate(tau):
        transformed = _transform_mask(a[:, fault], graph.num_detectors, graph.num_observables, detector_perm)
        if not torch.equal(transformed, a[:, int(mapped_fault)]):
            return False
    return True


def _transform_mask(
    mask: torch.Tensor,
    num_detectors: int,
    num_observables: int,
    detector_perm: list[int],
) -> torch.Tensor:
    transformed = torch.zeros_like(mask)
    for detector, mapped in enumerate(detector_perm):
        transformed[int(mapped)] = mask[int(detector)]
    for obs in range(int(num_observables)):
        bit = int(num_detectors) + obs
        transformed[bit] = mask[bit]
    return transformed


def _orbits_from_permutations(num_faults: int, permutations: Iterable[list[int]]) -> torch.Tensor:
    parent = list(range(int(num_faults)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for permutation in permutations:
        for fault, mapped in enumerate(permutation):
            union(fault, int(mapped))
    roots = [find(fault) for fault in range(int(num_faults))]
    compact: dict[int, int] = {}
    return torch.tensor([compact.setdefault(root, len(compact)) for root in roots], dtype=torch.long)


def _transform_coord(
    coord: tuple[float, ...] | list[float],
    transform: Callable[[float, float], tuple[float, float]],
) -> tuple[float, ...]:
    values = [float(value) for value in coord]
    if len(values) < 2:
        return tuple(values)
    starts = list(range(0, len(values), 3)) if len(values) >= 3 else [0]
    for start in starts:
        if start + 1 >= len(values):
            continue
        values[start], values[start + 1] = transform(values[start], values[start + 1])
    return tuple(values)


def _coord_key(coord: Iterable[float]) -> tuple[float, ...]:
    return tuple(round(float(value), 6) for value in coord)


def _boundary_role(coords: tuple[float, ...], metadata: dict[str, object]) -> str | None:
    all_coords = list(metadata.get("data_qubit_coords", [])) + list(metadata.get("meas_qubit_coords", []))
    if not all_coords or len(coords) < 2:
        return None
    xs = [float(coord[0]) for coord in all_coords]
    ys = [float(coord[1]) for coord in all_coords]
    x, y = float(coords[0]), float(coords[1])
    labels = []
    if abs(x - min(xs)) < 1e-6:
        labels.append("min_x")
    if abs(x - max(xs)) < 1e-6:
        labels.append("max_x")
    if abs(y - min(ys)) < 1e-6:
        labels.append("min_y")
    if abs(y - max(ys)) < 1e-6:
        labels.append("max_y")
    return "|".join(labels) if labels else "interior"


def _patch_center(metadata: dict[str, object], patch_id: str) -> tuple[float, float] | None:
    match = re.search(r"_at_q(-?\d+(?:\.\d+)?)_(-?\d+(?:\.\d+)?)$", patch_id)
    if match:
        return float(match.group(1)), float(match.group(2))
    coords = metadata.get("data_qubit_coords", [])
    if coords:
        xs = [float(coord[0]) for coord in coords]
        ys = [float(coord[1]) for coord in coords]
        return sum(xs) / len(xs), sum(ys) / len(ys)
    return None


def _distance_from_patch(patch_id: str) -> int | None:
    match = re.search(r"d(\d+)_", patch_id)
    return int(match.group(1)) if match else None
