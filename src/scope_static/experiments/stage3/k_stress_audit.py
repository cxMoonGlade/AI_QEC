from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scope_static.mechanism_discovery.discovery_model import DEFAULT_FINAL_TEMPERATURE
from scope_static.mechanism_discovery.discovery_model import DEFAULT_INITIAL_TEMPERATURE
from scope_static.mechanism_discovery.discovery_model import DEFAULT_MAX_ITER
from scope_static.mechanism_discovery.discovery_model import DEFAULT_OPERATION_CONTEXT_WEIGHT
from scope_static.mechanism_discovery.discovery_model import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3B1_DIR
from scope_static.mechanism_discovery.generator_learning import DEFAULT_MAX_CV_FOLDS
from scope_static.mechanism_discovery.generator_learning import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3C_DIR
from scope_static.mechanism_discovery.k_stress_audit import (
    DEFAULT_MIN_GENERATION_NULL_LIFT,
    DEFAULT_MIN_SUCCESS_ARI,
    DEFAULT_MIN_SUCCESS_BA,
    DEFAULT_MIN_SUCCESS_NMI,
    DEFAULT_MIN_UNDERCOMPLETE_NMI_GAP,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_OVERCOMPLETE_MULTIPLIER,
    DEFAULT_SEED,
    DEFAULT_UNDERCOMPLETE_FRACTION,
    run_stage3d4_k_stress_audit,
)
from scope_static.mechanism_discovery.observability_ceiling import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A5_DIR
from scope_static.mechanism_discovery.protocol_freeze import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A_DIR


def run_stage3d4_k_stress_audit_from_config(
    *,
    config_path: str | Path | None = None,
    stage3a_dir: str | Path | None = None,
    stage3a5_dir: str | Path | None = None,
    stage3b1_dir: str | Path | None = None,
    stage3c_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, object]:
    cfg = _load_config(config_path)
    s3a = Path(stage3a_dir) if stage3a_dir is not None else Path(str(cfg.get("stage3a_dir", DEFAULT_STAGE3A_DIR)))
    s3a5 = Path(stage3a5_dir) if stage3a5_dir is not None else Path(str(cfg.get("stage3a5_dir", DEFAULT_STAGE3A5_DIR)))
    s3b1 = Path(stage3b1_dir) if stage3b1_dir is not None else Path(str(cfg.get("stage3b1_dir", DEFAULT_STAGE3B1_DIR)))
    if stage3c_dir is not None:
        s3c = Path(stage3c_dir)
    elif "stage3c_dir" in cfg and cfg.get("stage3c_dir") is None:
        s3c = None
    else:
        s3c = Path(str(cfg.get("stage3c_dir", DEFAULT_STAGE3C_DIR)))
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", DEFAULT_OUTPUT_DIR)))
    result = run_stage3d4_k_stress_audit(
        stage3a_dir=s3a,
        stage3a5_dir=s3a5,
        stage3b1_dir=s3b1,
        stage3c_dir=s3c,
        output_dir=output,
        teacher_dir=None if cfg.get("teacher_dir") is None else Path(str(cfg.get("teacher_dir"))),
        seed=int(cfg.get("seed", DEFAULT_SEED)),
        max_iter=int(cfg.get("max_iter", DEFAULT_MAX_ITER)),
        max_cv_folds=None if cfg.get("max_cv_folds") is None else int(cfg.get("max_cv_folds", DEFAULT_MAX_CV_FOLDS)),
        initial_temperature=float(cfg.get("initial_temperature", DEFAULT_INITIAL_TEMPERATURE)),
        final_temperature=float(cfg.get("final_temperature", DEFAULT_FINAL_TEMPERATURE)),
        variance_floor=float(cfg.get("variance_floor", 1.0e-6)),
        undercomplete_fraction=float(cfg.get("undercomplete_fraction", DEFAULT_UNDERCOMPLETE_FRACTION)),
        overcomplete_multiplier=float(cfg.get("overcomplete_multiplier", DEFAULT_OVERCOMPLETE_MULTIPLIER)),
        min_success_nmi=float(cfg.get("min_success_nmi", DEFAULT_MIN_SUCCESS_NMI)),
        min_success_ari=float(cfg.get("min_success_ari", DEFAULT_MIN_SUCCESS_ARI)),
        min_success_ba=float(cfg.get("min_success_ba", DEFAULT_MIN_SUCCESS_BA)),
        min_undercomplete_nmi_gap=float(cfg.get("min_undercomplete_nmi_gap", DEFAULT_MIN_UNDERCOMPLETE_NMI_GAP)),
        min_generation_null_lift=float(cfg.get("min_generation_null_lift", DEFAULT_MIN_GENERATION_NULL_LIFT)),
        operation_context_weight=float(cfg.get("operation_context_weight", DEFAULT_OPERATION_CONTEXT_WEIGHT)),
    )
    summary = dict(result.get("k_stress_summary", {}))
    print(
        "Stage 3D.4 K-stress audit complete\n"
        f"  decision={result.get('decision')}\n"
        f"  global_null_categorical_population_nll={summary.get('global_null_categorical_population_nll')}\n"
        f"  best_success_exact_nmi={summary.get('best_success_exact_nmi')}\n"
        f"  best_undercomplete_exact_nmi={summary.get('best_undercomplete_exact_nmi')}\n"
        f"  undercomplete_nmi_gap={summary.get('undercomplete_nmi_gap')}\n"
        f"  output={output}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run Stage 3D.4 K undercomplete/exact/overcomplete stress audit.")
    parser.add_argument("--config", type=Path, default=Path("configs/scope_static/stage3d4_k_stress_audit.yaml"))
    parser.add_argument("--stage3a-dir", type=Path)
    parser.add_argument("--stage3a5-dir", type=Path)
    parser.add_argument("--stage3b1-dir", type=Path)
    parser.add_argument("--stage3c-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    run_stage3d4_k_stress_audit_from_config(
        config_path=args.config,
        stage3a_dir=args.stage3a_dir,
        stage3a5_dir=args.stage3a5_dir,
        stage3b1_dir=args.stage3b1_dir,
        stage3c_dir=args.stage3c_dir,
        output_dir=args.output_dir,
    )


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
        raise ValueError("Stage 3D.4 config must be a mapping")
    section = data.get("stage3d4_k_stress_audit", data)
    if not isinstance(section, dict):
        raise ValueError("Stage 3D.4 config section must be a mapping")
    return dict(section)


if __name__ == "__main__":
    main()
