from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import json
import math
import re
from pathlib import Path
from typing import Iterable

import numpy as np
import stim


SCHEMA_VERSION = "google_inventory_v1"

DATASET_REPETITION_D29 = "google_72Q_repetition_code_d29"
DATASET_SURFACE_SET1 = "google_72Q_surface_code_d3_d5_set1"
DATASET_SURFACE_SET2 = "google_72Q_surface_code_d3_d5_set2"
DATASET_105Q = "google_105Q_surface_code_d3_d5_d7"

DATASET_NAMES = (
    DATASET_REPETITION_D29,
    DATASET_SURFACE_SET1,
    DATASET_SURFACE_SET2,
    DATASET_105Q,
)

DEFAULT_DATASET_ROOTS: dict[str, Path] = {
    DATASET_REPETITION_D29: Path("/home/cx/Document/google_72Q_repetition_code_d29"),
    DATASET_SURFACE_SET1: Path("/home/cx/Document/google_72Q_surface_code_d3_d5_set1"),
    DATASET_SURFACE_SET2: Path("/home/cx/Document/google_72Q_surface_code_d3_d5_set2"),
    DATASET_105Q: Path("/home/cx/Document/google_105Q_surface_code_d3_d5_d7"),
}

DATASET_FAMILIES: dict[str, str] = {
    DATASET_REPETITION_D29: "repetition",
    DATASET_SURFACE_SET1: "surface",
    DATASET_SURFACE_SET2: "surface",
    DATASET_105Q: "surface",
}

EXPECTED_LEAF_COUNTS: dict[str, int] = {
    DATASET_REPETITION_D29: 200,
    DATASET_SURFACE_SET1: 3780,
    DATASET_SURFACE_SET2: 4641,
    DATASET_105Q: 420,
}

EXPECTED_DECODER_PATHWAYS: dict[str, tuple[str, ...]] = {
    DATASET_REPETITION_D29: ("MWPM_decoder_with_RL_optimized_prior",),
    DATASET_SURFACE_SET1: (
        "correlated_matching_decoder_with_rl_optimized_prior",
        "correlated_matching_decoder_with_si1000_prior",
        "harmony_decoder_with_rl_optimized_prior",
        "harmony_decoder_with_si1000_prior",
    ),
    DATASET_SURFACE_SET2: (
        "belief_matching_decoder_with_prior_from_detector_correlations",
        "belief_matching_decoder_with_rl_optimized_prior",
        "belief_matching_decoder_with_uninformative_prior",
        "correlated_matching_decoder_with_prior_from_detector_correlations",
        "correlated_matching_decoder_with_rl_optimized_prior",
        "correlated_matching_decoder_with_uninformative_prior",
        "harmony_decoder_with_prior_from_detector_correlations",
        "harmony_decoder_with_rl_optimized_prior",
        "harmony_decoder_with_uninformative_prior",
    ),
    DATASET_105Q: (
        "correlated_matching_decoder_with_rl_optimized_prior",
        "correlated_matching_decoder_with_si1000_prior",
        "harmony_decoder_with_rl_optimized_prior",
        "harmony_decoder_with_si1000_prior",
        "libra_decoder_with_rl_optimized_prior",
    ),
}

DECODER_ALIASES: dict[str, str] = {
    "decoder_si1000": "correlated_matching_decoder_with_si1000_prior",
    "matching_si1000": "correlated_matching_decoder_with_si1000_prior",
    "decoder_rl": "correlated_matching_decoder_with_rl_optimized_prior",
    "matching_rl": "correlated_matching_decoder_with_rl_optimized_prior",
    "harmony_si1000": "harmony_decoder_with_si1000_prior",
    "harmony_rl": "harmony_decoder_with_rl_optimized_prior",
    "mwpm_rl": "MWPM_decoder_with_RL_optimized_prior",
    "libra_rl": "libra_decoder_with_rl_optimized_prior",
}

REQUIRED_LEAF_FILE_FIELDS = (
    "circuit_ideal",
    "circuit_noisy_si1000",
    "measurements",
    "sweep_bits",
    "detection_events",
    "obs_flips_actual",
    "metadata",
)

FORBIDDEN_TRUE_LABELS = (
    "true_per_shot_physical_error_mechanism",
    "true_hidden_fault_partition",
    "true_public_FM_label",
    "true_legacy_catalog_id",
    "true_catalog_M_id",
    "catalog_M_label",
    "public_FM_label",
    "legacy_catalog_id",
)

LABEL_CLAIM_BOUNDARY = (
    "Google inventory labels expose hardware context, decoder outputs, strong shot labels, "
    "and DEM-derived proxy labels only. They are not true physical mechanism labels, "
    "hidden fault partitions, public F/M labels, or legacy catalog-ID labels."
)


@dataclass(frozen=True)
class GoogleLeaf:
    dataset_name: str
    dataset_family: str
    root: Path
    path: Path
    context_id: str
    sample_id: str | None
    sample_index: int | None
    patch_id: str | None
    basis: str
    distance: int | None
    rounds: int | None
    rounds_label: str
    shots: int | None
    circuit_ideal: Path
    circuit_noisy_si1000: Path
    measurements: Path
    sweep_bits: Path
    detection_events: Path
    obs_flips_actual: Path
    metadata: Path

    def decoder_dir(self, pathway_name: str) -> Path:
        return self.path / "decoding_results" / normalize_decoder_pathway(self.dataset_name, pathway_name)

    def decoder_error_model(self, pathway_name: str) -> Path:
        return self.decoder_dir(pathway_name) / "error_model.dem"

    def decoder_predictions(self, pathway_name: str) -> Path:
        return self.decoder_dir(pathway_name) / "obs_flips_predicted.b8"

    def required_files(self) -> dict[str, Path]:
        return {field: getattr(self, field) for field in REQUIRED_LEAF_FILE_FIELDS}

    def to_manifest_row(self) -> dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "dataset_name": self.dataset_name,
            "dataset_family": self.dataset_family,
            "root": str(self.root),
            "path": str(self.path),
            "context_id": self.context_id,
            "sample_id": self.sample_id,
            "sample_index": self.sample_index,
            "patch_id": self.patch_id,
            "basis": self.basis,
            "distance": self.distance,
            "rounds": self.rounds,
            "rounds_label": self.rounds_label,
            "shots": self.shots,
            "circuit_ideal": str(self.circuit_ideal),
            "circuit_noisy_si1000": str(self.circuit_noisy_si1000),
            "measurements": str(self.measurements),
            "sweep_bits": str(self.sweep_bits),
            "detection_events": str(self.detection_events),
            "obs_flips_actual": str(self.obs_flips_actual),
            "metadata": str(self.metadata),
            "required_files_available": {
                field: path.is_file() for field, path in self.required_files().items()
            },
        }


@dataclass(frozen=True)
class GoogleDecoderPathway:
    context_id: str
    dataset_name: str
    pathway_name: str
    decoder_family: str
    prior_family: str
    error_model_path: Path
    obs_flips_predicted_path: Path
    available_dem: bool
    available_predictions: bool

    def to_manifest_row(self, *, dem_proxy: dict[str, object] | None = None) -> dict[str, object]:
        row: dict[str, object] = {
            "schema_version": SCHEMA_VERSION,
            "context_id": self.context_id,
            "dataset_name": self.dataset_name,
            "pathway_name": self.pathway_name,
            "decoder_family": self.decoder_family,
            "prior_family": self.prior_family,
            "error_model_path": str(self.error_model_path),
            "obs_flips_predicted_path": str(self.obs_flips_predicted_path),
            "available_dem": self.available_dem,
            "available_predictions": self.available_predictions,
        }
        if dem_proxy is not None:
            row["dem_proxy_labels"] = dem_proxy
        return row


def normalize_decoder_pathway(dataset_name: str, pathway_name: str) -> str:
    text = str(pathway_name)
    if dataset_name in {DATASET_SURFACE_SET1, DATASET_105Q, DATASET_SURFACE_SET2, DATASET_REPETITION_D29}:
        return DECODER_ALIASES.get(text, text)
    return text


def decoder_pathway_metadata(pathway_name: str) -> dict[str, str]:
    name = str(pathway_name)
    lower = name.lower()
    if lower.startswith("mwpm_decoder"):
        decoder = "mwpm"
    elif lower.startswith("correlated_matching_decoder"):
        decoder = "correlated_matching"
    elif lower.startswith("belief_matching_decoder"):
        decoder = "belief_matching"
    elif lower.startswith("harmony_decoder"):
        decoder = "harmony"
    elif lower.startswith("libra_decoder"):
        decoder = "libra"
    else:
        decoder = name.split("_decoder", maxsplit=1)[0] if "_decoder" in name else "unknown"

    if "si1000" in lower:
        prior = "si1000"
    elif "rl_optimized" in lower:
        prior = "rl_optimized"
    elif "prior_from_detector_correlations" in lower:
        prior = "detector_correlations"
    elif "uninformative_prior" in lower:
        prior = "uninformative"
    else:
        prior = "unknown"
    return {"decoder_family": decoder, "prior_family": prior}


def google_context_id(
    *,
    dataset_name: str,
    sample_id: str | None,
    patch_id: str | None,
    basis: str,
    rounds_label: str,
) -> str:
    return "__".join(
        _safe_id(part)
        for part in (
            dataset_name,
            sample_id if sample_id is not None else "sample_null",
            patch_id if patch_id is not None else "patch_null",
            basis,
            rounds_label,
        )
    )


def normalize_google_dataset_root(root: str | Path, dataset_name: str) -> Path:
    if dataset_name not in DATASET_NAMES:
        raise ValueError(f"unknown Google dataset_name: {dataset_name}")
    start = Path(root).expanduser()
    candidates = (start, start / dataset_name)
    for candidate in candidates:
        if _looks_like_dataset_root(candidate, dataset_name):
            return candidate.resolve()
    checked = ", ".join(str(candidate) for candidate in candidates)
    raise ValueError(f"{dataset_name} root not found; checked {checked}")


def iter_google_leaves(root: str | Path, dataset_name: str) -> list[GoogleLeaf]:
    dataset_root = normalize_google_dataset_root(root, dataset_name)
    if dataset_name == DATASET_REPETITION_D29:
        return _iter_repetition_leaves(dataset_root)
    if dataset_name in {DATASET_SURFACE_SET1, DATASET_SURFACE_SET2}:
        return _iter_sampled_surface_leaves(dataset_root, dataset_name)
    if dataset_name == DATASET_105Q:
        return _iter_105q_leaves(dataset_root)
    raise ValueError(f"unknown Google dataset_name: {dataset_name}")


def iter_all_google_leaves(
    dataset_roots: dict[str, str | Path] | None = None,
    *,
    dataset_names: Iterable[str] | None = None,
) -> list[GoogleLeaf]:
    roots = {**DEFAULT_DATASET_ROOTS, **(dataset_roots or {})}
    names = tuple(dataset_names or DATASET_NAMES)
    leaves: list[GoogleLeaf] = []
    for dataset_name in names:
        leaves.extend(iter_google_leaves(roots[dataset_name], dataset_name))
    return leaves


def decoder_pathways_for_leaf(leaf: GoogleLeaf) -> list[GoogleDecoderPathway]:
    decoder_root = leaf.path / "decoding_results"
    names = set(EXPECTED_DECODER_PATHWAYS.get(leaf.dataset_name, ()))
    if decoder_root.is_dir():
        names.update(path.name for path in decoder_root.iterdir() if path.is_dir() and not _is_zone_identifier(path))
    pathways = []
    for name in sorted(names):
        metadata = decoder_pathway_metadata(name)
        error_model = decoder_root / name / "error_model.dem"
        predictions = decoder_root / name / "obs_flips_predicted.b8"
        pathways.append(
            GoogleDecoderPathway(
                context_id=leaf.context_id,
                dataset_name=leaf.dataset_name,
                pathway_name=name,
                decoder_family=metadata["decoder_family"],
                prior_family=metadata["prior_family"],
                error_model_path=error_model,
                obs_flips_predicted_path=predictions,
                available_dem=error_model.is_file(),
                available_predictions=predictions.is_file(),
            )
        )
    return pathways


def load_context_manifest(path: str | Path) -> list[dict[str, object]]:
    return _read_jsonl(path)


def load_decoder_manifest(path: str | Path) -> list[dict[str, object]]:
    return _read_jsonl(path)


def select_context_rows(
    rows: Iterable[dict[str, object]],
    *,
    dataset_name: str | None = None,
    dataset_family: str | None = None,
    sample_id: str | None = None,
    patch_id: str | None = None,
    basis: str | None = None,
    distance: int | None = None,
    rounds: int | None = None,
) -> list[dict[str, object]]:
    selected = []
    for row in rows:
        if dataset_name and row.get("dataset_name") != dataset_name:
            continue
        if dataset_family and row.get("dataset_family") != dataset_family:
            continue
        if sample_id and row.get("sample_id") != sample_id:
            continue
        if patch_id and row.get("patch_id") != patch_id:
            continue
        if basis and row.get("basis") != basis:
            continue
        if distance is not None and _optional_int(row.get("distance")) != int(distance):
            continue
        if rounds is not None and _optional_int(row.get("rounds")) != int(rounds):
            continue
        selected.append(row)
    return selected


def write_google_inventory_artifacts(
    *,
    output_dir: str | Path,
    dataset_roots: dict[str, str | Path] | None = None,
    dataset_names: Iterable[str] | None = None,
    dem_proxy_mode: str = "none",
) -> dict[str, object]:
    if dem_proxy_mode not in {"none", "first_per_dataset", "all"}:
        raise ValueError("dem_proxy_mode must be none, first_per_dataset, or all")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    names = tuple(dataset_names or DATASET_NAMES)
    roots = {**DEFAULT_DATASET_ROOTS, **(dataset_roots or {})}
    leaves: list[GoogleLeaf] = []
    missing_roots: dict[str, str] = {}
    for dataset_name in names:
        try:
            leaves.extend(iter_google_leaves(roots[dataset_name], dataset_name))
        except (FileNotFoundError, ValueError) as exc:
            missing_roots[dataset_name] = str(exc)

    context_path = output / "google_context_manifest.jsonl"
    decoder_path = output / "google_decoder_manifest.jsonl"
    label_path = output / "google_label_manifest.json"
    audit_path = output / "google_preprocessing_audit.json"

    decoder_rows: list[dict[str, object]] = []
    proxied_datasets: set[str] = set()
    with context_path.open("w", encoding="utf-8") as handle:
        for leaf in leaves:
            handle.write(json.dumps(leaf.to_manifest_row(), sort_keys=True) + "\n")
    with decoder_path.open("w", encoding="utf-8") as handle:
        for leaf in leaves:
            for pathway in decoder_pathways_for_leaf(leaf):
                dem_proxy = None
                if pathway.available_dem and _should_extract_proxy(dem_proxy_mode, pathway.dataset_name, proxied_datasets):
                    dem_proxy = extract_dem_proxy_labels(
                        pathway.error_model_path,
                        dataset_name=leaf.dataset_name,
                        context_id=leaf.context_id,
                        pathway_name=pathway.pathway_name,
                    )
                    proxied_datasets.add(pathway.dataset_name)
                row = pathway.to_manifest_row(dem_proxy=dem_proxy)
                decoder_rows.append(row)
                handle.write(json.dumps(row, sort_keys=True) + "\n")

    label_manifest = google_label_manifest(leaves)
    audit = google_preprocessing_audit(leaves, decoder_rows, missing_roots=missing_roots)
    label_path.write_text(json.dumps(label_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "context_manifest_path": str(context_path),
        "decoder_manifest_path": str(decoder_path),
        "label_manifest_path": str(label_path),
        "audit_path": str(audit_path),
        "num_contexts": len(leaves),
        "num_decoder_rows": len(decoder_rows),
        "audit": audit,
    }


def google_label_manifest(leaves: Iterable[GoogleLeaf] = ()) -> dict[str, object]:
    contexts = []
    for leaf in leaves:
        contexts.append(
            {
                "context_id": leaf.context_id,
                "dataset_name": leaf.dataset_name,
                "dataset_family": leaf.dataset_family,
                "sample_id": leaf.sample_id,
                "patch_id": leaf.patch_id,
                "basis": leaf.basis,
                "distance": leaf.distance,
                "rounds": leaf.rounds,
                "rounds_label": leaf.rounds_label,
                "shots": leaf.shots,
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "claim_boundary": LABEL_CLAIM_BOUNDARY,
        "label_layers": {
            "context_labels": [
                "dataset_name",
                "dataset_family",
                "sample_id",
                "patch_id",
                "basis",
                "distance",
                "rounds",
                "shots",
                "qubit_coordinates",
            ],
            "strong_shot_labels": ["obs_flips_actual", "obs_flips_actual_xor_obs_flips_predicted"],
            "decoder_labels": ["decoder_family", "prior_family", "decoder_pathway"],
            "dem_proxy_labels": [
                "fault_count",
                "detector_count",
                "observable_count",
                "support_size_distribution",
                "touches_logical",
                "detector_degree",
                "detector_coordinate_coverage",
                "boundary_bulk_proxy",
                "graph_component_proxy",
            ],
            "forbidden_true_labels": list(FORBIDDEN_TRUE_LABELS),
        },
        "contexts": contexts,
    }


def google_preprocessing_audit(
    leaves: Iterable[GoogleLeaf],
    decoder_rows: Iterable[dict[str, object]],
    *,
    missing_roots: dict[str, str] | None = None,
) -> dict[str, object]:
    leaf_list = list(leaves)
    decoder_list = list(decoder_rows)
    by_dataset: dict[str, dict[str, object]] = {}
    missing_files: dict[str, dict[str, object]] = {}
    for dataset_name in DATASET_NAMES:
        dataset_leaves = [leaf for leaf in leaf_list if leaf.dataset_name == dataset_name]
        by_dataset[dataset_name] = {
            "num_leaves": len(dataset_leaves),
            "expected_leaves": EXPECTED_LEAF_COUNTS.get(dataset_name),
            "leaf_count_matches_observed_inventory": len(dataset_leaves) == EXPECTED_LEAF_COUNTS.get(dataset_name),
            "samples": _sorted_optional_values(leaf.sample_id for leaf in dataset_leaves),
            "patches": _sorted_optional_values(leaf.patch_id for leaf in dataset_leaves),
            "bases": sorted({leaf.basis for leaf in dataset_leaves}),
            "distances": sorted({leaf.distance for leaf in dataset_leaves if leaf.distance is not None}),
            "rounds": sorted({leaf.rounds for leaf in dataset_leaves if leaf.rounds is not None}),
            "rounds_labels": sorted({leaf.rounds_label for leaf in dataset_leaves}),
            "shots": sorted({leaf.shots for leaf in dataset_leaves if leaf.shots is not None}),
        }
        missing_files[dataset_name] = _missing_file_audit(dataset_leaves)

    coverage: dict[str, dict[str, dict[str, int]]] = defaultdict(dict)
    for row in decoder_list:
        dataset = str(row["dataset_name"])
        pathway = str(row["pathway_name"])
        item = coverage[dataset].setdefault(
            pathway,
            {"rows": 0, "available_dem": 0, "available_predictions": 0, "missing_dem": 0, "missing_predictions": 0},
        )
        item["rows"] += 1
        if row.get("available_dem"):
            item["available_dem"] += 1
        else:
            item["missing_dem"] += 1
        if row.get("available_predictions"):
            item["available_predictions"] += 1
        else:
            item["missing_predictions"] += 1

    return {
        "schema_version": SCHEMA_VERSION,
        "claim_boundary": LABEL_CLAIM_BOUNDARY,
        "missing_roots": missing_roots or {},
        "datasets": by_dataset,
        "missing_required_leaf_files": missing_files,
        "decoder_coverage": {dataset: dict(pathways) for dataset, pathways in sorted(coverage.items())},
        "forbidden_true_labels": list(FORBIDDEN_TRUE_LABELS),
    }


def load_google_circuit(leaf: GoogleLeaf, *, noisy: bool = False) -> stim.Circuit:
    return stim.Circuit.from_file(str(leaf.circuit_noisy_si1000 if noisy else leaf.circuit_ideal))


def load_google_observations(leaf: GoogleLeaf, *, max_shots: int | None = None) -> np.ndarray:
    circuit = load_google_circuit(leaf)
    detectors = _read_b8_bits(leaf.detection_events, circuit.num_detectors)
    observables = _read_b8_bits(leaf.obs_flips_actual, circuit.num_observables)
    if detectors.shape[0] != observables.shape[0]:
        raise ValueError("detection_events.b8 and obs_flips_actual.b8 have different shot counts")
    observations = np.concatenate([detectors, observables], axis=1)
    if max_shots is not None:
        observations = observations[: int(max_shots)]
    return np.ascontiguousarray(observations)


def observation_shape_audit(leaf: GoogleLeaf) -> dict[str, object]:
    circuit = load_google_circuit(leaf)
    detectors = _read_b8_bits(leaf.detection_events, circuit.num_detectors)
    observables = _read_b8_bits(leaf.obs_flips_actual, circuit.num_observables)
    return {
        "context_id": leaf.context_id,
        "num_detector_bits": int(circuit.num_detectors),
        "num_observable_bits": int(circuit.num_observables),
        "detection_events_shape": [int(value) for value in detectors.shape],
        "obs_flips_actual_shape": [int(value) for value in observables.shape],
        "shot_count_matches": bool(detectors.shape[0] == observables.shape[0]),
        "detector_count_matches": bool(detectors.shape[1] == circuit.num_detectors),
        "observable_count_matches": bool(observables.shape[1] == circuit.num_observables),
    }


def extract_dem_proxy_labels(
    error_model_path: str | Path,
    *,
    dataset_name: str | None = None,
    context_id: str | None = None,
    pathway_name: str | None = None,
) -> dict[str, object]:
    path = Path(error_model_path)
    if not path.is_file():
        return {
            "proxy_label_only": True,
            "available": False,
            "error_model_path": str(path),
            "missing": True,
        }
    dem = stim.DetectorErrorModel.from_file(str(path))
    detector_coords = _dem_detector_coordinates(dem)
    num_detectors = int(dem.num_detectors)
    num_observables = int(dem.num_observables)
    degree = [0 for _ in range(num_detectors)]
    support_sizes: list[int] = []
    detector_support_sizes: list[int] = []
    touches_logical = 0
    fault_detector_sets: list[tuple[int, ...]] = []
    uf = _UnionFind(num_detectors)
    boundary_ids = _boundary_detector_ids(detector_coords)
    region_counts: Counter[str] = Counter()

    for instruction in dem.flattened():
        if instruction.type != "error":
            continue
        detectors: set[int] = set()
        observables: set[int] = set()
        for target in instruction.targets_copy():
            if target.is_separator():
                continue
            if target.is_relative_detector_id():
                detector = int(target.val)
                if 0 <= detector < num_detectors:
                    detectors.add(detector)
            elif target.is_logical_observable_id():
                observables.add(int(target.val))
        for detector in detectors:
            degree[detector] += 1
        detector_tuple = tuple(sorted(detectors))
        fault_detector_sets.append(detector_tuple)
        if len(detector_tuple) > 1:
            first = detector_tuple[0]
            for detector in detector_tuple[1:]:
                uf.union(first, detector)
        support_sizes.append(len(detectors) + len(observables))
        detector_support_sizes.append(len(detectors))
        if observables:
            touches_logical += 1
        region_counts[_fault_region(detectors, detector_coords, boundary_ids)] += 1

    component_ids = _component_ids(uf, num_detectors)
    component_counts: Counter[str] = Counter()
    for detectors in fault_detector_sets:
        if not detectors:
            component_counts["no_detector_targets"] += 1
            continue
        ids = sorted({component_ids[detector] for detector in detectors})
        component_counts[str(ids[0] if len(ids) == 1 else "multi_component")] += 1

    fault_count = len(support_sizes)
    return {
        "schema_version": SCHEMA_VERSION,
        "proxy_label_only": True,
        "available": True,
        "dataset_name": dataset_name,
        "context_id": context_id,
        "pathway_name": pathway_name,
        "dem_source_path": str(path),
        "fault_count": int(fault_count),
        "detector_count": int(num_detectors),
        "observable_count": int(num_observables),
        "support_size_distribution": _numeric_distribution(support_sizes),
        "detector_support_size_distribution": _numeric_distribution(detector_support_sizes),
        "touches_logical_count": int(touches_logical),
        "touches_logical_fraction": float(touches_logical / fault_count) if fault_count else 0.0,
        "detector_degree_distribution": _numeric_distribution(degree),
        "detector_coordinate_coverage": float(len(detector_coords) / num_detectors) if num_detectors else 1.0,
        "boundary_bulk_proxy": dict(sorted(region_counts.items())),
        "graph_component_proxy": {
            "num_detector_components": len(set(component_ids.values())) if num_detectors else 0,
            "fault_component_histogram": dict(sorted(component_counts.items())),
        },
        "forbidden_true_labels_absent": True,
    }


def set1_leaf_from_google_leaf(leaf: GoogleLeaf):
    if leaf.dataset_name != DATASET_SURFACE_SET1:
        raise ValueError("only Google Set1 leaves can be adapted to GoogleSet1Leaf")
    from .set1 import GoogleSet1Leaf

    if leaf.sample_id is None or leaf.patch_id is None:
        raise ValueError("Google Set1 leaves require sample_id and patch_id")
    return GoogleSet1Leaf(
        root=leaf.root,
        sample_id=leaf.sample_id,
        patch_id=leaf.patch_id,
        basis=leaf.basis,
        rounds_label=leaf.rounds_label,
    )


def _iter_repetition_leaves(root: Path) -> list[GoogleLeaf]:
    leaves: list[GoogleLeaf] = []
    for basis_dir in _iter_dirs(root):
        if basis_dir.name not in {"X", "Z"}:
            continue
        for sample_dir in _iter_dirs(basis_dir):
            if not sample_dir.name.startswith("sample_"):
                continue
            metadata = sample_dir / "metadata.json"
            if not metadata.is_file():
                continue
            meta = _read_json(metadata)
            sample_id = sample_dir.name
            rounds = _optional_int(meta.get("cycles"))
            rounds_label = f"r{rounds}" if rounds is not None else "runknown"
            leaves.append(
                _leaf(
                    dataset_name=DATASET_REPETITION_D29,
                    root=root,
                    path=sample_dir,
                    sample_id=sample_id,
                    patch_id=None,
                    basis=basis_dir.name,
                    distance=_optional_int(meta.get("distance")),
                    rounds=rounds,
                    rounds_label=rounds_label,
                    shots=_optional_int(meta.get("shots")),
                )
            )
    return sorted(leaves, key=lambda leaf: (leaf.basis, leaf.sample_id or ""))


def _iter_sampled_surface_leaves(root: Path, dataset_name: str) -> list[GoogleLeaf]:
    leaves: list[GoogleLeaf] = []
    for sample_dir in _iter_dirs(root):
        if not sample_dir.name.startswith("sample_"):
            continue
        for patch_dir in _iter_dirs(sample_dir):
            for basis_dir in _iter_dirs(patch_dir):
                if basis_dir.name not in {"X", "Z"}:
                    continue
                for rounds_dir in _iter_dirs(basis_dir):
                    if not rounds_dir.name.startswith("r"):
                        continue
                    metadata = rounds_dir / "metadata.json"
                    if not metadata.is_file():
                        continue
                    meta = _read_json(metadata)
                    leaves.append(
                        _leaf(
                            dataset_name=dataset_name,
                            root=root,
                            path=rounds_dir,
                            sample_id=sample_dir.name,
                            patch_id=patch_dir.name,
                            basis=basis_dir.name,
                            distance=_optional_int(meta.get("distance")) or _distance_from_patch(patch_dir.name),
                            rounds=_optional_int(meta.get("rounds")) or _rounds_from_label(rounds_dir.name),
                            rounds_label=rounds_dir.name,
                            shots=_optional_int(meta.get("shots")),
                        )
                    )
    return sorted(leaves, key=lambda leaf: (leaf.sample_id or "", leaf.patch_id or "", leaf.basis, leaf.rounds or -1))


def _iter_105q_leaves(root: Path) -> list[GoogleLeaf]:
    leaves: list[GoogleLeaf] = []
    for patch_dir in _iter_dirs(root):
        if not patch_dir.name.startswith("d"):
            continue
        for basis_dir in _iter_dirs(patch_dir):
            if basis_dir.name not in {"X", "Z"}:
                continue
            for rounds_dir in _iter_dirs(basis_dir):
                if not rounds_dir.name.startswith("r"):
                    continue
                metadata = rounds_dir / "metadata.json"
                if not metadata.is_file():
                    continue
                meta = _read_json(metadata)
                leaves.append(
                    _leaf(
                        dataset_name=DATASET_105Q,
                        root=root,
                        path=rounds_dir,
                        sample_id=None,
                        patch_id=patch_dir.name,
                        basis=basis_dir.name,
                        distance=_optional_int(meta.get("distance")) or _distance_from_patch(patch_dir.name),
                        rounds=_optional_int(meta.get("rounds")) or _rounds_from_label(rounds_dir.name),
                        rounds_label=rounds_dir.name,
                        shots=_optional_int(meta.get("shots")),
                    )
                )
    return sorted(leaves, key=lambda leaf: (leaf.patch_id or "", leaf.basis, leaf.rounds or -1))


def _leaf(
    *,
    dataset_name: str,
    root: Path,
    path: Path,
    sample_id: str | None,
    patch_id: str | None,
    basis: str,
    distance: int | None,
    rounds: int | None,
    rounds_label: str,
    shots: int | None,
) -> GoogleLeaf:
    return GoogleLeaf(
        dataset_name=dataset_name,
        dataset_family=DATASET_FAMILIES[dataset_name],
        root=root,
        path=path,
        context_id=google_context_id(
            dataset_name=dataset_name,
            sample_id=sample_id,
            patch_id=patch_id,
            basis=basis,
            rounds_label=rounds_label,
        ),
        sample_id=sample_id,
        sample_index=_sample_index(sample_id),
        patch_id=patch_id,
        basis=basis,
        distance=distance,
        rounds=rounds,
        rounds_label=rounds_label,
        shots=shots,
        circuit_ideal=path / "circuit_ideal.stim",
        circuit_noisy_si1000=path / "circuit_noisy_si1000.stim",
        measurements=path / "measurements.b8",
        sweep_bits=path / "sweep_bits.b8",
        detection_events=path / "detection_events.b8",
        obs_flips_actual=path / "obs_flips_actual.b8",
        metadata=path / "metadata.json",
    )


def _looks_like_dataset_root(path: Path, dataset_name: str) -> bool:
    if not path.is_dir():
        return False
    if dataset_name == DATASET_REPETITION_D29:
        return (path / "X").is_dir() and (path / "Z").is_dir()
    if dataset_name in {DATASET_SURFACE_SET1, DATASET_SURFACE_SET2}:
        return any(child.is_dir() and child.name.startswith("sample_") for child in path.iterdir())
    if dataset_name == DATASET_105Q:
        return any(child.is_dir() and child.name.startswith("d") for child in path.iterdir())
    return False


def _should_extract_proxy(mode: str, dataset_name: str, proxied_datasets: set[str]) -> bool:
    if mode == "none":
        return False
    if mode == "all":
        return True
    return dataset_name not in proxied_datasets


def _missing_file_audit(leaves: list[GoogleLeaf]) -> dict[str, object]:
    counts = Counter()
    examples: dict[str, list[str]] = defaultdict(list)
    for leaf in leaves:
        for field, path in leaf.required_files().items():
            if not path.is_file():
                counts[field] += 1
                if len(examples[field]) < 5:
                    examples[field].append(str(path))
    return {
        "missing_counts": dict(sorted(counts.items())),
        "examples": {field: values for field, values in sorted(examples.items())},
    }


def _read_b8_bits(path: Path, bits_per_shot: int) -> np.ndarray:
    return stim.read_shot_data_file(path=str(path), format="b8", num_measurements=int(bits_per_shot)).astype(
        np.bool_, copy=False
    )


def _dem_detector_coordinates(dem: stim.DetectorErrorModel) -> dict[int, tuple[float, ...]]:
    try:
        coords = dem.get_detector_coordinates()
    except Exception:
        return {}
    return {int(index): tuple(float(value) for value in values) for index, values in coords.items()}


def _boundary_detector_ids(coords: dict[int, tuple[float, ...]]) -> set[int]:
    if not coords:
        return set()
    dim = max((len(value) for value in coords.values()), default=0)
    if dim == 0:
        return set()
    padded = {
        detector: tuple(list(values) + [0.0] * (dim - len(values)))
        for detector, values in coords.items()
    }
    mins = [min(values[axis] for values in padded.values()) for axis in range(dim)]
    maxs = [max(values[axis] for values in padded.values()) for axis in range(dim)]
    boundary = set()
    axes = range(min(2, dim))
    for detector, values in padded.items():
        if any(math.isclose(values[axis], mins[axis]) or math.isclose(values[axis], maxs[axis]) for axis in axes):
            boundary.add(detector)
    return boundary


def _fault_region(
    detectors: set[int],
    coords: dict[int, tuple[float, ...]],
    boundary_ids: set[int],
) -> str:
    if not detectors:
        return "no_detector_targets"
    if not coords:
        return "unknown_detector_coords"
    if any(detector not in coords for detector in detectors):
        return "unknown_detector_coords"
    return "boundary_touching" if any(detector in boundary_ids for detector in detectors) else "bulk_only"


def _component_ids(uf: "_UnionFind", count: int) -> dict[int, int]:
    roots = sorted({uf.find(index) for index in range(count)})
    mapping = {root: idx for idx, root in enumerate(roots)}
    return {index: mapping[uf.find(index)] for index in range(count)}


class _UnionFind:
    def __init__(self, count: int):
        self.parent = list(range(count))
        self.rank = [0] * count

    def find(self, value: int) -> int:
        parent = self.parent[value]
        if parent != value:
            self.parent[value] = self.find(parent)
        return self.parent[value]

    def union(self, left: int, right: int) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return
        if self.rank[left_root] < self.rank[right_root]:
            left_root, right_root = right_root, left_root
        self.parent[right_root] = left_root
        if self.rank[left_root] == self.rank[right_root]:
            self.rank[left_root] += 1


def _numeric_distribution(values: Iterable[int]) -> dict[str, object]:
    items = [int(value) for value in values]
    if not items:
        return {"count": 0, "min": None, "max": None, "mean": None, "histogram": {}}
    hist = Counter(items)
    return {
        "count": len(items),
        "min": min(items),
        "max": max(items),
        "mean": float(sum(items) / len(items)),
        "histogram": {str(key): int(hist[key]) for key in sorted(hist)},
    }


def _iter_dirs(path: Path) -> list[Path]:
    return sorted(child for child in path.iterdir() if child.is_dir() and not _is_zone_identifier(child))


def _is_zone_identifier(path: Path) -> bool:
    return path.name.endswith(":Zone.Identifier")


def _read_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_jsonl(path: str | Path) -> list[dict[str, object]]:
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _sample_index(sample_id: str | None) -> int | None:
    if sample_id is None:
        return None
    match = re.search(r"(\d+)$", sample_id)
    return int(match.group(1)) if match else None


def _distance_from_patch(patch_id: str | None) -> int | None:
    if not patch_id:
        return None
    match = re.match(r"d(\d+)_", str(patch_id))
    return int(match.group(1)) if match else None


def _rounds_from_label(rounds_label: str) -> int | None:
    match = re.search(r"(\d+)$", str(rounds_label))
    return int(match.group(1)) if match else None


def _sorted_optional_values(values: Iterable[str | None]) -> list[str | None]:
    present = sorted({value for value in values if value is not None})
    return present if present else [None]


def _safe_id(value: object) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value)).strip("-") or "none"
