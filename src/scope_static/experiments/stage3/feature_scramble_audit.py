from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scope_static.mechanism_discovery.discovery_model import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3B1_DIR
from scope_static.mechanism_discovery.feature_scramble_audit import (
    DEFAULT_MIN_CATEGORICAL_NLL_DEGRADATION,
    DEFAULT_MIN_COLLAPSE_FRACTION,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SCRAMBLE_COUNT,
    DEFAULT_SEED,
    run_stage3d2_feature_scramble_audit,
)
from scope_static.mechanism_discovery.generator_learning import DEFAULT_MAX_CV_FOLDS
from scope_static.mechanism_discovery.generator_learning import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3C_DIR
from scope_static.mechanism_discovery.observability_ceiling import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A5_DIR
from scope_static.mechanism_discovery.protocol_freeze import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A_DIR


def run_stage3d2_feature_scramble_audit_from_config(
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
    result = run_stage3d2_feature_scramble_audit(
        stage3a_dir=s3a,
        stage3a5_dir=s3a5,
        stage3b1_dir=s3b1,
        stage3c_dir=s3c,
        output_dir=output,
        seed=int(cfg.get("seed", DEFAULT_SEED)),
        scramble_count=int(cfg.get("scramble_count", DEFAULT_SCRAMBLE_COUNT)),
        max_cv_folds=None if cfg.get("max_cv_folds") is None else int(cfg.get("max_cv_folds", DEFAULT_MAX_CV_FOLDS)),
        variance_floor=float(cfg.get("variance_floor", 1.0e-6)),
        min_categorical_nll_degradation=float(
            cfg.get("min_categorical_nll_degradation", DEFAULT_MIN_CATEGORICAL_NLL_DEGRADATION)
        ),
        min_collapse_fraction=float(cfg.get("min_collapse_fraction", DEFAULT_MIN_COLLAPSE_FRACTION)),
    )
    collapse = dict(dict(result.get("feature_scramble_metrics", {})).get("primary_collapse_report", {}))
    print(
        "Stage 3D.2 feature-scramble audit complete\n"
        f"  decision={result.get('decision')}\n"
        f"  original_categorical_population_nll={collapse.get('original_assignment')}\n"
        f"  scrambled_mean_categorical_population_nll={collapse.get('scrambled_feature_mean')}\n"
        f"  global_null_categorical_population_nll={collapse.get('global_null')}\n"
        f"  collapse_fraction={collapse.get('collapse_fraction_toward_global_null')}\n"
        f"  output={output}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run Stage 3D.2 feature-scramble generator audit.")
    parser.add_argument("--config", type=Path, default=Path("configs/scope_static/stage3d2_feature_scramble_audit.yaml"))
    parser.add_argument("--stage3a-dir", type=Path)
    parser.add_argument("--stage3a5-dir", type=Path)
    parser.add_argument("--stage3b1-dir", type=Path)
    parser.add_argument("--stage3c-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    run_stage3d2_feature_scramble_audit_from_config(
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
        raise ValueError("Stage 3D.2 config must be a mapping")
    section = data.get("stage3d2_feature_scramble_audit", data)
    if not isinstance(section, dict):
        raise ValueError("Stage 3D.2 config section must be a mapping")
    return dict(section)


if __name__ == "__main__":
    main()
