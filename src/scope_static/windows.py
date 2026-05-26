from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from statistics import mean

from .fault_graph import FaultGraph


@dataclass(frozen=True)
class ObservationWindow:
    name: str
    bits: tuple[int, ...]
    kind: str

    @property
    def size(self) -> int:
        return len(self.bits)


@dataclass(frozen=True)
class WindowPlan:
    """Constructed observation windows plus their reproducibility audit."""

    windows: tuple[ObservationWindow, ...]
    config: dict[str, object]

    @classmethod
    def from_config(cls, graph: FaultGraph, config: dict[str, object] | None) -> "WindowPlan":
        cfg = dict(config or {})
        return cls(windows=tuple(_build_windows_from_config_dict(graph, cfg)), config=cfg)

    def detector_only(self, graph: FaultGraph) -> "WindowPlan":
        return WindowPlan(
            windows=tuple(detector_only_windows(graph, list(self.windows))),
            config=self.config,
        )

    def audit_dict(self) -> dict[str, object]:
        audit = window_audit_dict(list(self.windows))
        builders = self.config.get("builders", ["detector_geometry"]) if bool(self.config.get("enabled", False)) else []
        audit["window_plan_enabled"] = bool(self.config.get("enabled", False))
        audit["window_plan_builders"] = [str(builder) for builder in builders]
        return audit

    def __iter__(self):
        return iter(self.windows)

    def __len__(self) -> int:
        return len(self.windows)

    def __getitem__(self, index: int) -> ObservationWindow:
        return self.windows[index]


def make_window(name: str, bits: tuple[int, ...] | list[int], kind: str) -> ObservationWindow:
    return ObservationWindow(name=name, bits=tuple(sorted(set(int(bit) for bit in bits))), kind=kind)


def dedupe_windows(
    windows: list[ObservationWindow],
    *,
    max_window_bits: int | None = None,
) -> list[ObservationWindow]:
    seen: set[tuple[int, ...]] = set()
    result: list[ObservationWindow] = []
    for window in windows:
        if not window.bits:
            continue
        if max_window_bits is not None and window.size > int(max_window_bits):
            continue
        if window.bits in seen:
            continue
        seen.add(window.bits)
        result.append(window)
    return result


def build_windows_from_detector_geometry(
    graph: FaultGraph,
    *,
    include_single_detectors: bool = True,
    include_detector_pairs: bool = True,
    include_radius1: bool = True,
    include_boundary_logical: bool = True,
    radius: float = 1.0,
    max_window_bits: int = 8,
) -> list[ObservationWindow]:
    windows: list[ObservationWindow] = []
    if include_single_detectors:
        windows.extend(
            make_window(f"detector:{detector}", [detector], "single_detector")
            for detector in range(graph.num_detectors)
        )

    if include_detector_pairs:
        windows.extend(_detector_pair_windows_from_faults(graph))

    if include_radius1 and graph.detector_coordinates is not None and graph.num_detectors:
        windows.extend(_radius_windows_from_coordinates(graph, radius=radius))

    if include_boundary_logical and graph.num_observables:
        windows.extend(_boundary_logical_windows(graph, max_window_bits=max_window_bits))

    return dedupe_windows(windows, max_window_bits=max_window_bits)


def build_windows_from_template_motifs(
    graph: FaultGraph,
    *,
    max_window_bits: int = 8,
) -> list[ObservationWindow]:
    windows: list[ObservationWindow] = []
    template_ids = graph.template_ids.tolist()
    for template in sorted(set(int(value) for value in template_ids)):
        fault_ids = [fault for fault, value in enumerate(template_ids) if int(value) == template]
        bits = _bits_touched_by_faults(graph, fault_ids)
        if bits:
            windows.append(make_window(f"template:{template}", bits, "template_motif"))
        for fault in fault_ids:
            windows.append(make_window(f"template:{template}:fault:{fault}", graph.supports_by_fault[fault], "template_fault"))
    return dedupe_windows(windows, max_window_bits=max_window_bits)


def build_windows_from_orbits(
    graph: FaultGraph,
    *,
    max_window_bits: int = 8,
) -> list[ObservationWindow]:
    windows: list[ObservationWindow] = []
    orbit_ids = graph.orbit_ids.tolist()
    for orbit in sorted(set(int(value) for value in orbit_ids)):
        fault_ids = [fault for fault, value in enumerate(orbit_ids) if int(value) == orbit]
        bits = _bits_touched_by_faults(graph, fault_ids)
        if bits:
            windows.append(make_window(f"orbit:{orbit}", bits, "orbit"))
        for fault in fault_ids:
            windows.append(make_window(f"orbit:{orbit}:fault:{fault}", graph.supports_by_fault[fault], "orbit_fault"))
    return dedupe_windows(windows, max_window_bits=max_window_bits)


def build_windows_from_config(graph: FaultGraph, config: dict[str, object] | None) -> list[ObservationWindow]:
    return list(WindowPlan.from_config(graph, config).windows)


def _build_windows_from_config_dict(graph: FaultGraph, cfg: dict[str, object]) -> list[ObservationWindow]:
    if not bool(cfg.get("enabled", False)):
        return []
    max_window_bits = int(cfg.get("max_window_bits", 8))
    builders = cfg.get("builders", ["detector_geometry"])
    windows: list[ObservationWindow] = []
    if "detector_geometry" in builders:
        windows.extend(
            build_windows_from_detector_geometry(
                graph,
                include_single_detectors=bool(cfg.get("include_single_detectors", True)),
                include_detector_pairs=bool(cfg.get("include_detector_pairs", True)),
                include_radius1=bool(cfg.get("include_radius1", True)),
                include_boundary_logical=bool(cfg.get("include_boundary_logical", True)),
                radius=float(cfg.get("radius", 1.0)),
                max_window_bits=max_window_bits,
            )
        )
    if "template_motifs" in builders:
        windows.extend(build_windows_from_template_motifs(graph, max_window_bits=max_window_bits))
    if "orbits" in builders:
        windows.extend(build_windows_from_orbits(graph, max_window_bits=max_window_bits))
    windows = dedupe_windows(windows, max_window_bits=max_window_bits)
    max_windows = cfg.get("max_windows")
    if max_windows is not None:
        windows = windows[: int(max_windows)]
    return windows


def window_audit_dict(windows: list[ObservationWindow]) -> dict[str, object]:
    sizes = [window.size for window in windows]
    kinds = sorted(set(window.kind for window in windows))
    return {
        "num_windows": len(windows),
        "window_kinds": kinds,
        "max_window_bits": max(sizes) if sizes else 0,
        "mean_window_bits": float(mean(sizes)) if sizes else 0.0,
    }


def window_coverage_audit_dict(graph: FaultGraph, windows: list[ObservationWindow]) -> dict[str, object]:
    """Audit observation-bit and effective-fault coverage for local windows."""

    audit = window_audit_dict(windows)
    covered_bits: set[int] = set()
    covered_faults: set[int] = set()
    kind_counts: dict[str, int] = {}
    local_patterns: dict[tuple[object, ...], int] = {}
    for window in windows:
        covered_bits.update(window.bits)
        kind_counts[window.kind] = kind_counts.get(window.kind, 0) + 1
        fault_ids, mask_states = graph.project_window(window.bits)
        covered_faults.update(int(fault) for fault in fault_ids.tolist())
        pattern_key = (
            window.kind,
            window.size,
            tuple(sorted(int(value) for value in mask_states.cpu().tolist())),
        )
        local_patterns[pattern_key] = local_patterns.get(pattern_key, 0) + 1
    audit.update(
        {
            "detector_logical_bit_coverage": {
                "num_bits_covered": len(covered_bits),
                "num_bits_total": graph.B,
                "fraction_bits_covered": float(len(covered_bits) / graph.B) if graph.B else 0.0,
                "fraction_observation_bits_covered": float(len(covered_bits) / graph.B) if graph.B else 0.0,
            },
            "fraction_dem_faults_active": float(len(covered_faults) / graph.M) if graph.M else 0.0,
            "num_dem_faults_active": len(covered_faults),
            "num_dem_faults_total": graph.M,
            "window_type_counts": {key: int(kind_counts[key]) for key in sorted(kind_counts)},
            "num_single_detector_windows": int(kind_counts.get("single_detector", 0)),
            "num_pair_windows": int(kind_counts.get("detector_pair", 0)),
            "num_radius_or_local_motif_windows": sum(
                int(count)
                for kind, count in kind_counts.items()
                if kind.startswith("radius") or "motif" in kind or kind.startswith("template")
            ),
            "repeated_local_pattern_count": sum(1 for count in local_patterns.values() if count > 1),
        }
    )
    return audit


def detector_only_windows(graph: FaultGraph, windows: list[ObservationWindow]) -> list[ObservationWindow]:
    return [window for window in windows if all(bit < graph.num_detectors for bit in window.bits)]


def _detector_pair_windows_from_faults(graph: FaultGraph) -> list[ObservationWindow]:
    pairs: set[tuple[int, int]] = set()
    for support in graph.supports_by_fault:
        detector_bits = [bit for bit in support if bit < graph.num_detectors]
        for left, right in combinations(detector_bits, 2):
            pairs.add((min(left, right), max(left, right)))
    return [make_window(f"detector_pair:{left}:{right}", [left, right], "detector_pair") for left, right in sorted(pairs)]


def _radius_windows_from_coordinates(graph: FaultGraph, *, radius: float) -> list[ObservationWindow]:
    coords = graph.detector_coordinates
    if coords is None:
        return []
    windows: list[ObservationWindow] = []
    for detector in range(graph.num_detectors):
        center = coords[detector]
        nearby = []
        for other in range(graph.num_detectors):
            distance = (coords[other] - center).abs().max().item()
            if distance <= float(radius):
                nearby.append(other)
        windows.append(make_window(f"radius1:{detector}", nearby, "radius1_detector_geometry"))
    return windows


def _boundary_logical_windows(graph: FaultGraph, *, max_window_bits: int) -> list[ObservationWindow]:
    windows: list[ObservationWindow] = []
    for obs in range(graph.num_observables):
        logical_bit = graph.num_detectors + obs
        fault_ids = graph.faults_by_observation_bit[logical_bit]
        bits = _bits_touched_by_faults(graph, fault_ids)
        if len(bits) <= max_window_bits:
            windows.append(make_window(f"logical:{obs}", bits, "boundary_logical"))
        for fault in fault_ids:
            windows.append(make_window(f"logical:{obs}:fault:{fault}", graph.supports_by_fault[fault], "boundary_logical_fault"))
    return windows


def _bits_touched_by_faults(graph: FaultGraph, fault_ids: list[int] | tuple[int, ...]) -> list[int]:
    bits: set[int] = set()
    for fault in fault_ids:
        bits.update(graph.supports_by_fault[int(fault)])
    return sorted(bits)
