from __future__ import annotations

"""Evaluator-only source-timeline sidecars for simulator runs."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Literal, Mapping

from ..source.process import SOURCE_TIMELINE_SCHEMA, SourceTimeline
from .artifacts import ArtifactPaths, file_sha256, write_json


CycleBinding = Literal["qec_round", "circuit_tick", "external_cycle"]
ShotBinding = Literal["shared_across_shots", "continuous_acquisition"]
SOURCE_TIMELINE_BINDING_SCHEMA = "error_coupling_simulator.frontend.source_timeline_binding.v1"


@dataclass(frozen=True)
class SourceTimelineBinding:
    """Declare how a source timeline is aligned to a simulator run.

    By default this is an artifact contract only: it records exact source truth
    without lowering it into Stim, DEM, MCWF, or joint-Lindbladian records. A
    frontend projection may pass an explicit execution status that says a
    declared reduced carrier was applied to records.
    """

    cycle_binding: CycleBinding = "external_cycle"
    shot_binding: ShotBinding = "shared_across_shots"
    payload_keys: tuple[str, ...] = ()
    schedule_windows: tuple[dict[str, Any], ...] = ()
    schema: str = SOURCE_TIMELINE_BINDING_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != SOURCE_TIMELINE_BINDING_SCHEMA:
            raise ValueError(
                f"unsupported source timeline binding schema {self.schema!r}; "
                f"expected {SOURCE_TIMELINE_BINDING_SCHEMA!r}"
            )
        if self.cycle_binding not in {"qec_round", "circuit_tick", "external_cycle"}:
            raise ValueError(
                "cycle_binding must be 'qec_round', 'circuit_tick', or 'external_cycle'"
            )
        if self.shot_binding not in {"shared_across_shots", "continuous_acquisition"}:
            raise ValueError("shot_binding must be 'shared_across_shots' or 'continuous_acquisition'")
        if self.shot_binding == "continuous_acquisition":
            raise NotImplementedError(
                "shot_binding='continuous_acquisition' requires an explicit shot/acquisition axis; "
                "SourceTimeline currently carries cycle-axis arrays only"
            )
        if isinstance(self.payload_keys, (str, bytes)):
            raise ValueError("payload_keys must be a sequence of payload-key strings, not one string")
        if self.schedule_windows:
            raise NotImplementedError(
                "schedule_windows are not executable in the Stim frontend yet; "
                "leave this empty until tick-duration/window lowering exists"
            )
        object.__setattr__(self, "payload_keys", tuple(str(k) for k in self.payload_keys))
        object.__setattr__(
            self,
            "schedule_windows",
            tuple(dict(window) for window in self.schedule_windows),
        )

    def to_manifest(
        self,
        *,
        timeline: SourceTimeline,
        compiled_metadata: Mapping[str, Any],
        shots: int,
    ) -> dict[str, Any]:
        inferred = infer_source_binding_context(compiled_metadata)
        _validate_binding(self, timeline=timeline, inferred=inferred)
        payload_keys = self.payload_keys or tuple(timeline.payload.keys())
        missing = set(payload_keys) - set(timeline.payload)
        if missing:
            raise KeyError(f"source binding payload_keys missing from timeline: {sorted(missing)!r}")
        return {
            "schema": self.schema,
            "visibility": "evaluator_only",
            "cycle_binding": self.cycle_binding,
            "shot_binding": self.shot_binding,
            "shots": int(shots),
            "n_cycles": int(timeline.n_cycles),
            "cycle_time_ns": float(timeline.cycle_time_ns),
            "payload_keys": list(payload_keys),
            "schedule_windows": list(self.schedule_windows),
            "inferred_context": inferred,
            "execution_status": _source_sidecar_only_status(),
        }


def default_source_timeline_binding(compiled_metadata: Mapping[str, Any]) -> SourceTimelineBinding:
    """Choose the narrowest default binding supported by compiler metadata."""

    inferred = infer_source_binding_context(compiled_metadata)
    if inferred.get("code_rounds") is not None:
        return SourceTimelineBinding(cycle_binding="qec_round")
    return SourceTimelineBinding(cycle_binding="external_cycle")


def infer_source_binding_context(compiled_metadata: Mapping[str, Any]) -> dict[str, Any]:
    """Extract public schedule/layout facts relevant to source-timeline alignment."""

    metadata = dict(compiled_metadata)
    code_spec = metadata.get("code_spec")
    schedule = metadata.get("schedule")
    qubit_coords = metadata.get("qubit_coords")
    return {
        "compiler": metadata.get("compiler"),
        "schedule_name": schedule.get("name") if isinstance(schedule, Mapping) else None,
        "code_name": code_spec.get("name") if isinstance(code_spec, Mapping) else None,
        "code_rounds": code_spec.get("rounds") if isinstance(code_spec, Mapping) else None,
        "num_qubit_coords": len(qubit_coords) if isinstance(qubit_coords, Mapping) else None,
    }


def write_source_timeline_sidecar(
    timeline: SourceTimeline,
    paths: ArtifactPaths,
    *,
    binding: SourceTimelineBinding | None,
    compiled_metadata: Mapping[str, Any],
    shots: int,
    execution_status: Mapping[str, Any] | None = None,
    projection_audit: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Write exact source truth and binding manifests for one simulator run.

    Returns ``(artifact_entries, evaluator_sidecar_entry, binding_manifest, public_stub)``.
    """

    binding_manifest = build_source_timeline_binding_manifest(
        timeline,
        binding=binding,
        compiled_metadata=compiled_metadata,
        shots=int(shots),
        execution_status=execution_status,
        projection_audit=projection_audit,
    )
    timeline_path = timeline.save_npz(paths.source_timeline)
    binding_manifest["source_timeline_file"] = paths.source_timeline.name
    binding_manifest["source_timeline_sha256"] = file_sha256(timeline_path)
    write_json(paths.source_timeline_binding, binding_manifest)

    artifacts = {
        "source_timeline": {
            "file": paths.source_timeline.name,
            "sha256": file_sha256(paths.source_timeline),
            "visibility": "evaluator_only",
            "schema": timeline.schema,
        },
        "source_timeline_binding": {
            "file": paths.source_timeline_binding.name,
            "sha256": file_sha256(paths.source_timeline_binding),
            "visibility": "evaluator_only",
            "schema": binding_manifest["schema"],
        },
    }
    sidecar = {
        "name": "axis2_source_timeline",
        "path": paths.source_timeline.name,
        "visibility": "evaluator_only",
        "binding_path": paths.source_timeline_binding.name,
        "role": "source_truth_for_replay_and_faithfulness_audit",
        "representability": (
            "source_timeline_plus_reduced_stim_pauli_projection"
            if binding_manifest["execution_status"].get("applied_to_stim_records")
            else "source_timeline_not_stim_pauli_noise"
        ),
        "applied_to_records": bool(
            binding_manifest["execution_status"].get("applied_to_stim_records", False)
        ),
    }
    return artifacts, sidecar, binding_manifest, source_binding_public_stub(binding_manifest)


def build_source_timeline_binding_manifest(
    timeline: SourceTimeline,
    *,
    binding: SourceTimelineBinding | None,
    compiled_metadata: Mapping[str, Any],
    shots: int,
    execution_status: Mapping[str, Any] | None = None,
    projection_audit: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate and build the source binding manifest without writing files."""

    bind = binding or default_source_timeline_binding(compiled_metadata)
    manifest = bind.to_manifest(
        timeline=timeline,
        compiled_metadata=compiled_metadata,
        shots=int(shots),
    )
    if execution_status is not None:
        manifest["execution_status"] = _normalize_execution_status(execution_status)
    if projection_audit is not None:
        manifest["projection_audit"] = _normalize_projection_audit(projection_audit)
    manifest["source_timeline"] = timeline.to_manifest()
    return manifest


def source_binding_public_stub(binding_manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Return the top-level manifest stub without source payload summaries."""

    return {
        "schema": binding_manifest["schema"],
        "visibility": "evaluator_only",
        "binding_artifact": "source_timeline_binding",
        "cycle_binding": binding_manifest["cycle_binding"],
        "shot_binding": binding_manifest["shot_binding"],
        "shots": int(binding_manifest["shots"]),
        "n_cycles": int(binding_manifest["n_cycles"]),
        "cycle_time_ns": float(binding_manifest["cycle_time_ns"]),
        "inferred_context": dict(binding_manifest["inferred_context"]),
        "execution_status": dict(binding_manifest["execution_status"]),
        "projection_audit_in_binding": "projection_audit" in binding_manifest,
    }


def load_source_timeline_from_manifest(
    out_dir: str | Path,
    manifest: Mapping[str, Any],
) -> SourceTimeline:
    """Load a source timeline sidecar after validating the manifest hash."""

    artifacts = manifest.get("artifacts", {})
    entry = artifacts.get("source_timeline")
    if not isinstance(entry, Mapping) or not entry.get("file"):
        raise ValueError("manifest does not contain a source_timeline artifact")
    if entry.get("schema") != SOURCE_TIMELINE_SCHEMA:
        raise ValueError(
            f"unsupported source timeline artifact schema {entry.get('schema')!r}; "
            f"expected {SOURCE_TIMELINE_SCHEMA!r}"
        )
    path = _artifact_path(out_dir, entry["file"], artifact_key="source_timeline")
    expected = entry.get("sha256")
    _require_sha("source_timeline.sha256", expected)
    actual = file_sha256(path)
    if actual != expected:
        raise ValueError(f"source_timeline sha256 mismatch: manifest={expected}, actual={actual}")
    binding_entry = artifacts.get("source_timeline_binding")
    if not isinstance(binding_entry, Mapping) or not binding_entry.get("file"):
        raise ValueError("manifest does not contain a source_timeline_binding artifact")
    if binding_entry.get("schema") != SOURCE_TIMELINE_BINDING_SCHEMA:
        raise ValueError(
            f"unsupported source timeline binding artifact schema "
            f"{binding_entry.get('schema')!r}; expected {SOURCE_TIMELINE_BINDING_SCHEMA!r}"
        )
    binding_path = _artifact_path(
        out_dir,
        binding_entry["file"],
        artifact_key="source_timeline_binding",
    )
    binding_expected = binding_entry.get("sha256")
    _require_sha("source_timeline_binding.sha256", binding_expected)
    binding_actual = file_sha256(binding_path)
    if binding_actual != binding_expected:
        raise ValueError(
            f"source_timeline_binding sha256 mismatch: manifest={binding_expected}, actual={binding_actual}"
        )
    binding_manifest = json.loads(binding_path.read_text())
    if binding_manifest.get("schema") != SOURCE_TIMELINE_BINDING_SCHEMA:
        raise ValueError(
            f"unsupported source timeline binding schema {binding_manifest.get('schema')!r}; "
            f"expected {SOURCE_TIMELINE_BINDING_SCHEMA!r}"
        )
    if binding_manifest.get("source_timeline_sha256") != actual:
        raise ValueError(
            "source_timeline_binding does not match source_timeline artifact: "
            f"binding={binding_manifest.get('source_timeline_sha256')}, actual={actual}"
        )
    return SourceTimeline.load_npz(path)


def _require_sha(name: str, value: Any) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"manifest artifact {name} must contain a 64-hex sha256")


def _artifact_path(out_dir: str | Path, filename: Any, *, artifact_key: str) -> Path:
    raw = str(filename)
    rel = Path(raw)
    if rel.is_absolute() or rel.name != raw or raw in {"", ".", ".."}:
        raise ValueError(f"manifest artifact {artifact_key!r} must be a relative basename, got {raw!r}")
    root = Path(out_dir).resolve()
    path = (root / rel).resolve()
    if path.parent != root:
        raise ValueError(f"manifest artifact {artifact_key!r} escapes run directory: {raw!r}")
    return path


def _validate_binding(
    binding: SourceTimelineBinding,
    *,
    timeline: SourceTimeline,
    inferred: Mapping[str, Any],
) -> None:
    if binding.cycle_binding == "qec_round":
        rounds = inferred.get("code_rounds")
        if rounds is None:
            raise ValueError("cycle_binding='qec_round' requires compiled CodeSpec rounds metadata")
        if int(rounds) != int(timeline.n_cycles):
            raise ValueError(
                "source timeline length does not match CodeSpec rounds for qec_round binding: "
                f"n_cycles={timeline.n_cycles}, rounds={rounds}"
            )
    elif binding.cycle_binding == "circuit_tick":
        # Executable Stim projections use discrete CircuitIR TICK indices. The
        # current frontend has no physical tick durations, so validation is
        # intentionally limited to declaring the integer index map honestly.
        return


def _source_sidecar_only_status() -> dict[str, Any]:
    return {
        "applied_to_stim_records": False,
        "stim_dem_modified": False,
        "backend_lowering": "not_implemented_in_stim_pauli_frontend",
        "reason": (
            "SourceTimeline is written as evaluator-only truth. It is not "
            "laundered into independent Stim Pauli noise or DEM faults."
        ),
    }


def _normalize_execution_status(status: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(status)
    out["applied_to_stim_records"] = bool(out.get("applied_to_stim_records", False))
    out["stim_dem_modified"] = bool(out.get("stim_dem_modified", False))
    out["backend_lowering"] = str(out.get("backend_lowering", "unspecified"))
    out["reason"] = str(out.get("reason", ""))
    return out


def _normalize_projection_audit(audit: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(audit)
    if out.get("visibility") != "evaluator_only":
        raise ValueError("source projection audit must be visibility='evaluator_only'")
    return out


__all__ = [
    "SourceTimelineBinding",
    "build_source_timeline_binding_manifest",
    "default_source_timeline_binding",
    "infer_source_binding_context",
    "load_source_timeline_from_manifest",
    "source_binding_public_stub",
    "write_source_timeline_sidecar",
]
