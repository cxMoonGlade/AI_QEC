from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import time
from typing import Any


@dataclass(frozen=True)
class PhysicalOracleStackPaths:
    root: Path
    preflight_dir: Path
    teacher_dir: Path
    separability_dir: Path
    local_inverse_dir: Path
    stack_json: Path
    stack_markdown: Path

    def as_dict(self) -> dict[str, str]:
        return {
            "root": str(self.root),
            "preflight_dir": str(self.preflight_dir),
            "teacher_dir": str(self.teacher_dir),
            "separability_dir": str(self.separability_dir),
            "local_inverse_dir": str(self.local_inverse_dir),
            "stack_json": str(self.stack_json),
            "stack_markdown": str(self.stack_markdown),
        }


def physical_oracle_stack_paths(output_dir: str | Path) -> PhysicalOracleStackPaths:
    root = Path(output_dir)
    return PhysicalOracleStackPaths(
        root=root,
        preflight_dir=root / "S2D_PHYS0_preflight",
        teacher_dir=root / "S2D_PHYS1_teacher",
        separability_dir=root / "S2D_PHYS2_oracle_separability",
        local_inverse_dir=root / "S2D_PHYS3_local_inverse",
        stack_json=root / "physical_oracle_stack.json",
        stack_markdown=root / "physical_oracle_stack.md",
    )


def run_physical_oracle_stack(
    config: dict[str, object] | None = None,
    *,
    output_dir: str | Path,
    bootstrap_replicates: int = 16,
    random_baseline_trials: int = 64,
    run_local_inverse: str = "auto",
) -> dict[str, object]:
    mode = str(run_local_inverse)
    if mode not in {"auto", "always"}:
        raise ValueError("run_local_inverse must be 'auto' or 'always'")
    cfg = dict(config or {})
    paths = physical_oracle_stack_paths(output_dir)
    paths.root.mkdir(parents=True, exist_ok=True)
    timings: dict[str, float] = {}
    total_start = time.perf_counter()

    start = time.perf_counter()
    teacher = _generate_physical_teacher_dataset(
        cfg,
        output_dir=paths.teacher_dir,
        preflight_dir=paths.preflight_dir,
    )
    timings["PHYS1_teacher"] = time.perf_counter() - start

    start = time.perf_counter()
    teacher_self = _run_oracle_separability_audit(
        teacher_dir=paths.teacher_dir,
        output_dir=paths.separability_dir,
        paper_informed=bool(cfg.get("paper_informed_ptm_features", True)),
    )
    timings["PHYS2_teacher_self"] = time.perf_counter() - start

    teacher_self_passed = _teacher_self_passes(teacher_self)
    local: dict[str, object] | None = None
    local_skip_reason = None
    if mode == "always" or teacher_self_passed:
        start = time.perf_counter()
        local = _run_physical_local_inverse_discovery(
            teacher_dir=paths.teacher_dir,
            separability_dir=paths.separability_dir,
            output_dir=paths.local_inverse_dir,
            config={
                **cfg,
                "num_clusters": len(teacher_self.get("oracle_label_names", [])),
                "bootstrap_replicates": int(bootstrap_replicates),
                "random_baseline_trials": int(random_baseline_trials),
            },
        )
        timings["PHYS3_learner"] = time.perf_counter() - start
    else:
        timings["PHYS3_learner"] = 0.0
        local_skip_reason = "teacher_self_probe_limited"

    teacher_metrics = _compact_teacher(teacher, paths)
    teacher_self_metrics = _compact_phys2(teacher_self)
    learner_metrics = _compact_phys3(local) if local is not None else None
    teacher_self_verdict = _teacher_self_verdict(teacher_self)
    learner_verdict = _learner_recovery_verdict(local, skip_reason=local_skip_reason)
    overall = _overall_diagnosis(teacher_self_passed=teacher_self_passed, local=local)
    timings["total"] = time.perf_counter() - total_start

    result: dict[str, object] = {
        "schema": "scope_static_physical_oracle_stack_v1",
        "stage": "Physical Oracle Stack",
        "output_dir": str(paths.root),
        "paths": paths.as_dict(),
        "run_local_inverse": mode,
        "teacher": teacher_metrics,
        "teacher_self": {
            **teacher_self_metrics,
            "verdict": teacher_self_verdict,
        },
        "learner": {
            "ran": local is not None,
            "skipped": local is None,
            "skip_reason": local_skip_reason,
            "verdict": learner_verdict,
            "metrics": learner_metrics,
        },
        "verdicts": {
            "teacher_self_verdict": teacher_self_verdict,
            "learner_recovery_verdict": learner_verdict,
            "overall_diagnosis": overall,
        },
        "metrics": {
            "teacher": teacher_metrics,
            "teacher_self": teacher_self_metrics,
            "learner": learner_metrics,
        },
        "timings_seconds": timings,
        "stage_results": {
            "teacher": teacher,
            "teacher_self": teacher_self,
            "learner": local,
        },
    }
    paths.stack_json.write_text(json.dumps(result, indent=2, sort_keys=True, default=_json_default) + "\n")
    paths.stack_markdown.write_text(format_physical_oracle_stack_summary(result))
    return result


def stack_stage_results(stack: dict[str, object]) -> dict[str, object]:
    paths = dict(stack.get("paths", {}))
    stages = dict(stack.get("stage_results", {}))
    return {
        "teacher_dir": Path(str(paths["teacher_dir"])),
        "separability_dir": Path(str(paths["separability_dir"])),
        "local_dir": Path(str(paths["local_inverse_dir"])),
        "teacher": stages.get("teacher"),
        "separability": stages.get("teacher_self"),
        "local": stages.get("learner"),
        "stack": stack,
    }


def load_phys1_teacher_artifact(teacher_dir: str | Path) -> dict[str, object]:
    import numpy as np

    root = Path(teacher_dir)
    mechanisms_path = root / "oracle_mechanisms.json"
    observations_path = root / "observations.npz"
    mechanisms = []
    if mechanisms_path.exists():
        raw = json.loads(mechanisms_path.read_text())
        mechanisms = list(raw.get("mechanisms", []))
    artifact: dict[str, object] = {
        "teacher_dir": str(root),
        "mechanisms": mechanisms,
        "num_locations": len(mechanisms),
    }
    if observations_path.exists():
        data = np.load(observations_path)
        artifact.update(
            {
                "observations_shape": [int(value) for value in data["observations"].shape],
                "probe_names": [str(value) for value in data["probe_names"].tolist()],
                "shots": int(data["shots"][0]) if "shots" in data else None,
            }
        )
    config_path = root / "teacher_config.json"
    if config_path.exists():
        artifact["teacher_config"] = json.loads(config_path.read_text())
    return artifact


def load_phys2_metrics(separability_dir: str | Path) -> dict[str, object]:
    return json.loads((Path(separability_dir) / "metrics.json").read_text())


def load_phys3_metrics(local_inverse_dir: str | Path) -> dict[str, object]:
    return json.loads((Path(local_inverse_dir) / "metrics.json").read_text())


def format_physical_oracle_stack_summary(result: dict[str, object]) -> str:
    verdicts = dict(result.get("verdicts", {}))
    teacher = dict(result.get("teacher", {}))
    teacher_self = dict(result.get("teacher_self", {}))
    learner = dict(result.get("learner", {}))
    timings = dict(result.get("timings_seconds", {}))
    lines = [
        "# Physical Oracle Stack",
        "",
        f"- Overall diagnosis: `{verdicts.get('overall_diagnosis')}`",
        f"- Teacher self-distinguishability: `{verdicts.get('teacher_self_verdict')}`",
        f"- Learner recovery: `{verdicts.get('learner_recovery_verdict')}`",
        f"- Qubits: `{teacher.get('num_qubits')}`",
        f"- Probes: `{teacher.get('num_probes')}`",
        f"- Shots: `{teacher.get('shots')}`",
        f"- Aer simulator: `{_format_aer(teacher.get('aer_simulator'))}`",
        f"- PHYS2 ARI/NMI: `{float(teacher_self.get('ari', 0.0)):.4f}` / `{float(teacher_self.get('nmi', 0.0)):.4f}`",
    ]
    if bool(learner.get("ran")) and isinstance(learner.get("metrics"), dict):
        metrics = dict(learner["metrics"])
        main = dict(metrics.get("main_result", {}))
        lines.append(f"- PHYS3 ARI/NMI: `{float(main.get('ari', 0.0)):.4f}` / `{float(main.get('nmi', 0.0)):.4f}`")
    else:
        lines.append(f"- PHYS3: `skipped ({learner.get('skip_reason')})`")
    lines.extend(
        [
            "",
            "| stage | seconds |",
            "| --- | ---: |",
        ]
    )
    for key in ("PHYS1_teacher", "PHYS2_teacher_self", "PHYS3_learner", "total"):
        lines.append(f"| {key} | {float(timings.get(key, 0.0)):.4f} |")
    lines.append("")
    return "\n".join(lines)


def _generate_physical_teacher_dataset(*args, **kwargs):
    from scope_static.physical.teacher import generate_physical_teacher_dataset

    return generate_physical_teacher_dataset(*args, **kwargs)


def _run_oracle_separability_audit(**kwargs):
    from scope_static.physical.separability import run_oracle_separability_audit

    return run_oracle_separability_audit(**kwargs)


def _run_physical_local_inverse_discovery(**kwargs):
    from scope_static.physical.local_inverse import run_physical_local_inverse_discovery

    return run_physical_local_inverse_discovery(**kwargs)


def _teacher_self_passes(metrics: dict[str, object]) -> bool:
    return float(metrics.get("ari", 0.0)) >= 0.85 and float(metrics.get("nmi", 0.0)) >= 0.85


def _teacher_self_verdict(metrics: dict[str, object]) -> str:
    if _teacher_self_passes(metrics):
        return "teacher_self_distinguishable"
    return "teacher_self_probe_limited"


def _learner_recovery_verdict(local: dict[str, object] | None, *, skip_reason: str | None) -> str:
    if local is None:
        return "not_run_teacher_probe_limited" if skip_reason else "not_run"
    return str(local.get("s2d3_result", local.get("acceptance_label", "learner_ran")))


def _overall_diagnosis(*, teacher_self_passed: bool, local: dict[str, object] | None) -> str:
    if not teacher_self_passed:
        return "probe_limited"
    if local is None:
        return "learner_not_run"
    main = local.get("main_result")
    if not isinstance(main, dict):
        return "learner_ran"
    ari = float(main.get("ari", 0.0))
    nmi = float(main.get("nmi", 0.0))
    active = int(main.get("active_clusters", 0))
    k = int(local.get("num_clusters", max(1, active)))
    bootstrap = local.get("bootstrap_nmi", {})
    boot = float(bootstrap.get("min_vs_full", 0.0)) if isinstance(bootstrap, dict) else 0.0
    if ari >= 0.85 and nmi >= 0.85 and active >= max(1, k - 1) and boot >= 0.80:
        return "strong_recovery"
    if ari >= 0.75 and nmi >= 0.90:
        return "near_strong"
    return "learner_limited"


def _compact_teacher(teacher: dict[str, object], paths: PhysicalOracleStackPaths) -> dict[str, object]:
    return {
        "stage": teacher.get("stage"),
        "output_dir": str(paths.teacher_dir),
        "num_probes": teacher.get("num_probes"),
        "num_qubits": teacher.get("num_qubits"),
        "shots": teacher.get("shots"),
        "mechanism_counts": teacher.get("mechanism_counts", {}),
        "num_circuit_batches": teacher.get("num_circuit_batches", 1),
        "balanced_min_instances_per_mechanism": teacher.get("balanced_min_instances_per_mechanism"),
        "aer_simulator": teacher.get("aer_simulator"),
        "backend_audit_dir": str(paths.preflight_dir),
        "active_probe_manifest": teacher.get("active_probe_manifest"),
        "noise_application_audit": teacher.get("noise_application_audit"),
        "non_clifford_teacher": teacher.get("non_clifford_teacher"),
        "warnings": teacher.get("warnings", []),
    }


def _compact_phys2(metrics: dict[str, object]) -> dict[str, object]:
    return {
        "ari": metrics.get("ari"),
        "nmi": metrics.get("nmi"),
        "active_clusters": metrics.get("active_clusters"),
        "separability_gate": metrics.get("separability_gate"),
        "oracle_label_names": metrics.get("oracle_label_names"),
        "feature_shape": metrics.get("feature_shape"),
        "num_locations": metrics.get("num_locations"),
        "weakest_pairwise_distances": _weakest_pairwise_distances(metrics),
    }


def _compact_phys3(metrics: dict[str, object] | None) -> dict[str, object] | None:
    if metrics is None:
        return None
    bootstrap = metrics.get("bootstrap_nmi", {})
    return {
        "s2d3_result": metrics.get("s2d3_result"),
        "acceptance_label": metrics.get("acceptance_label"),
        "num_clusters": metrics.get("num_clusters"),
        "main_result": metrics.get("main_result"),
        "physical_local_inverse_probability_v2_result": metrics.get("physical_local_inverse_probability_v2_result"),
        "direct_S_alpha_result": metrics.get("direct_S_alpha_result"),
        "oracle_fingerprint_upper_bound": metrics.get("oracle_fingerprint_upper_bound"),
        "prediction_metrics": metrics.get("prediction_metrics"),
        "nll_difficulty_audit": metrics.get("nll_difficulty_audit"),
        "bootstrap_nmi": {key: value for key, value in dict(bootstrap).items() if key != "labels"} if isinstance(bootstrap, dict) else {},
        "key_comparison": metrics.get("key_comparison"),
    }


def _weakest_pairwise_distances(metrics: dict[str, object], *, limit: int = 8) -> list[dict[str, object]]:
    raw = metrics.get("pairwise_mechanism_distance", {})
    if not isinstance(raw, dict):
        return []
    rows = [{"mechanism_pair": str(key), "distance": float(value)} for key, value in raw.items()]
    return sorted(rows, key=lambda item: item["distance"])[: int(limit)]


def _format_aer(value: object) -> str:
    if not isinstance(value, dict):
        return "unavailable"
    return f"method={value.get('method')} device={value.get('device')} reason={value.get('selection_reason')}"


def _json_default(value: object) -> Any:
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "item"):
        try:
            return value.item()  # type: ignore[no-any-return]
        except Exception:
            pass
    if hasattr(value, "tolist"):
        try:
            return value.tolist()  # type: ignore[no-any-return]
        except Exception:
            pass
    return str(value)
