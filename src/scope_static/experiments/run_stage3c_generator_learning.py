from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scope_static.physical.stage3a5_observability_ceiling import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A5_DIR
from scope_static.physical.stage3a_protocol_freeze import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A_DIR
from scope_static.physical.stage3b1_discovery_model import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3B1_DIR
from scope_static.physical.stage3c_generator_learning import (
    DEFAULT_MAX_CV_FOLDS,
    DEFAULT_OUTPUT_DIR,
    run_stage3c_prototype_generator_learning,
)


def run_stage3c_generator_learning_from_config(
    *,
    config_path: str | Path | None = None,
    stage3a_dir: str | Path | None = None,
    stage3a5_dir: str | Path | None = None,
    stage3b1_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    teacher_dir: str | Path | None = None,
) -> dict[str, object]:
    cfg = _load_config(config_path)
    s3a = Path(stage3a_dir) if stage3a_dir is not None else Path(str(cfg.get("stage3a_dir", DEFAULT_STAGE3A_DIR)))
    s3a5 = Path(stage3a5_dir) if stage3a5_dir is not None else Path(str(cfg.get("stage3a5_dir", DEFAULT_STAGE3A5_DIR)))
    s3b1 = Path(stage3b1_dir) if stage3b1_dir is not None else Path(str(cfg.get("stage3b1_dir", DEFAULT_STAGE3B1_DIR)))
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", DEFAULT_OUTPUT_DIR)))
    result = run_stage3c_prototype_generator_learning(
        stage3a_dir=s3a,
        stage3a5_dir=s3a5,
        stage3b1_dir=s3b1,
        output_dir=output,
        teacher_dir=None if teacher_dir is None and not cfg.get("teacher_dir") else Path(str(teacher_dir if teacher_dir is not None else cfg.get("teacher_dir"))),
        max_cv_folds=None if cfg.get("max_cv_folds") is None else int(cfg.get("max_cv_folds", DEFAULT_MAX_CV_FOLDS)),
        variance_floor=float(cfg.get("variance_floor", 1.0e-6)),
    )
    predicted = dict(dict(result.get("predicted_assignment_metrics", {})).get("overall", {}))
    print(
        "Stage 3C prototype generator learning complete\n"
        f"  decision={result.get('decision')}\n"
        f"  predicted_assignment_categorical_population_nll={predicted.get('categorical_population_nll')}\n"
        f"  predicted_assignment_gaussian_density_nll={predicted.get('gaussian_density_nll')}\n"
        f"  output={output}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run Stage 3C prototype and visible-generator learning.")
    parser.add_argument("--config", type=Path, default=Path("configs/scope_static/stage3c_generator_learning.yaml"))
    parser.add_argument("--stage3a-dir", type=Path)
    parser.add_argument("--stage3a5-dir", type=Path)
    parser.add_argument("--stage3b1-dir", type=Path)
    parser.add_argument("--teacher-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    run_stage3c_generator_learning_from_config(
        config_path=args.config,
        stage3a_dir=args.stage3a_dir,
        stage3a5_dir=args.stage3a5_dir,
        stage3b1_dir=args.stage3b1_dir,
        teacher_dir=args.teacher_dir,
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
        raise ValueError("Stage 3C config must be a mapping")
    section = data.get("stage3c_prototype_generator_learning", data)
    if not isinstance(section, dict):
        raise ValueError("Stage 3C config section must be a mapping")
    return dict(section)


if __name__ == "__main__":
    main()
