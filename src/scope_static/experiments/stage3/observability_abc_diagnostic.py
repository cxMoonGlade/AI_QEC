from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scope_static.mechanism_discovery.observability_abc_diagnostic import (
    DEFAULT_FEATURE_PROFILES,
    DEFAULT_MAX_CV_FOLDS,
    DEFAULT_MLP_EPOCHS,
    DEFAULT_MLP_HIDDEN_DIM,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PASS_MIN_RECALL,
    DEFAULT_SEED,
    DEFAULT_STAGE3A_DIR,
    DEFAULT_TARGET_GROUPS,
    DEFAULT_VQ_K_VALUES,
    run_stage3_abc_observability_diagnostic,
)


def run_stage3_abc_observability_diagnostic_from_config(
    *,
    config_path: str | Path | None = None,
    stage3a_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    teacher_dir: str | Path | None = None,
    enhanced_stage3a_dir: str | Path | None = None,
    enhanced_teacher_dir: str | Path | None = None,
    seed: int | None = None,
) -> dict[str, object]:
    cfg = _load_config(config_path)
    result = run_stage3_abc_observability_diagnostic(
        stage3a_dir=Path(stage3a_dir) if stage3a_dir is not None else Path(str(cfg.get("stage3a_dir", DEFAULT_STAGE3A_DIR))),
        output_dir=Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", DEFAULT_OUTPUT_DIR))),
        teacher_dir=_optional_path(teacher_dir if teacher_dir is not None else cfg.get("teacher_dir")),
        enhanced_stage3a_dir=_optional_path(
            enhanced_stage3a_dir if enhanced_stage3a_dir is not None else cfg.get("enhanced_stage3a_dir")
        ),
        enhanced_teacher_dir=_optional_path(
            enhanced_teacher_dir if enhanced_teacher_dir is not None else cfg.get("enhanced_teacher_dir")
        ),
        target_groups=cfg.get("target_groups", DEFAULT_TARGET_GROUPS),  # type: ignore[arg-type]
        feature_profiles=cfg.get("feature_profiles", DEFAULT_FEATURE_PROFILES),  # type: ignore[arg-type]
        vq_k_values=cfg.get("vq_k_values", DEFAULT_VQ_K_VALUES),  # type: ignore[arg-type]
        max_cv_folds=None if cfg.get("max_cv_folds", DEFAULT_MAX_CV_FOLDS) is None else int(cfg.get("max_cv_folds", DEFAULT_MAX_CV_FOLDS)),
        seed=int(seed if seed is not None else cfg.get("seed", DEFAULT_SEED)),
        mlp_epochs=int(cfg.get("mlp_epochs", DEFAULT_MLP_EPOCHS)),
        mlp_hidden_dim=int(cfg.get("mlp_hidden_dim", DEFAULT_MLP_HIDDEN_DIM)),
        pass_min_recall=float(cfg.get("pass_min_recall", DEFAULT_PASS_MIN_RECALL)),
        improvement_delta=float(cfg.get("improvement_delta", 0.05)),
    )
    decisions = dict(dict(result.get("abc_decision_audit", {})).get("rows", {}))
    print(
        "Stage 3 ABC observability diagnostic complete\n"
        f"  decision={result.get('decision')}\n"
        f"  enhanced_probe_ran={dict(result.get('abc_decision_audit', {})).get('enhanced_probe_ran')}\n"
        f"  target_count={len(decisions)}\n"
        f"  output={result.get('output_dir')}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run Stage 3 A/B/C observability diagnostics.")
    parser.add_argument("--config", type=Path, default=Path("configs/scope_static/stage3_abc_observability_diagnostic.yaml"))
    parser.add_argument("--stage3a-dir", type=Path)
    parser.add_argument("--teacher-dir", type=Path)
    parser.add_argument("--enhanced-stage3a-dir", type=Path)
    parser.add_argument("--enhanced-teacher-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--seed", type=int)
    args = parser.parse_args(argv)
    run_stage3_abc_observability_diagnostic_from_config(
        config_path=args.config,
        stage3a_dir=args.stage3a_dir,
        teacher_dir=args.teacher_dir,
        enhanced_stage3a_dir=args.enhanced_stage3a_dir,
        enhanced_teacher_dir=args.enhanced_teacher_dir,
        output_dir=args.output_dir,
        seed=args.seed,
    )


def _optional_path(value: object) -> Path | None:
    if value is None or not str(value):
        return None
    return Path(str(value))


def _load_config(config_path: str | Path | None) -> dict[str, object]:
    if config_path is None:
        return {}
    path = Path(config_path)
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text())
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Stage 3 ABC config must be a mapping")
    section = data.get("stage3_abc_observability_diagnostic", data)
    if not isinstance(section, dict):
        raise ValueError("Stage 3 ABC config section must be a mapping")
    return dict(section)


if __name__ == "__main__":
    main()
