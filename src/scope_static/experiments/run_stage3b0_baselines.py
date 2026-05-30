from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scope_static.physical.stage3a5_observability_ceiling import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A5_DIR
from scope_static.physical.stage3a_protocol_freeze import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A_DIR
from scope_static.physical.stage3b0_baselines import (
    DEFAULT_MAX_FULL_COV_FEATURES,
    DEFAULT_MAX_ITER,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SEED,
    run_stage3b0_nonlearned_clustering_baselines,
)


def run_stage3b0_baselines_from_config(
    *,
    config_path: str | Path | None = None,
    stage3a_dir: str | Path | None = None,
    stage3a5_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    teacher_dir: str | Path | None = None,
    seed: int | None = None,
) -> dict[str, object]:
    cfg = _load_config(config_path)
    s3a = Path(stage3a_dir) if stage3a_dir is not None else Path(str(cfg.get("stage3a_dir", DEFAULT_STAGE3A_DIR)))
    s3a5 = Path(stage3a5_dir) if stage3a5_dir is not None else Path(str(cfg.get("stage3a5_dir", DEFAULT_STAGE3A5_DIR)))
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", DEFAULT_OUTPUT_DIR)))
    result = run_stage3b0_nonlearned_clustering_baselines(
        stage3a_dir=s3a,
        stage3a5_dir=s3a5,
        output_dir=output,
        teacher_dir=None if teacher_dir is None and not cfg.get("teacher_dir") else Path(str(teacher_dir if teacher_dir is not None else cfg.get("teacher_dir"))),
        seed=int(seed if seed is not None else cfg.get("seed", DEFAULT_SEED)),
        max_iter=int(cfg.get("max_iter", DEFAULT_MAX_ITER)),
        max_full_cov_features=int(cfg.get("max_full_cov_features", DEFAULT_MAX_FULL_COV_FEATURES)),
    )
    summary = dict(result.get("learned_assignment_summary", {}))
    print(
        "Stage 3B.0 non-learned clustering baselines complete\n"
        f"  decision={result.get('decision')}\n"
        f"  primary_baseline={summary.get('primary_baseline')}\n"
        f"  primary_k_mode={summary.get('primary_k_mode')}\n"
        f"  output={output}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run Stage 3B.0 visible-only non-learned clustering baselines.")
    parser.add_argument("--config", type=Path, default=Path("configs/scope_static/stage3b0_baselines.yaml"))
    parser.add_argument("--stage3a-dir", type=Path)
    parser.add_argument("--stage3a5-dir", type=Path)
    parser.add_argument("--teacher-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--seed", type=int)
    args = parser.parse_args(argv)
    run_stage3b0_baselines_from_config(
        config_path=args.config,
        stage3a_dir=args.stage3a_dir,
        stage3a5_dir=args.stage3a5_dir,
        teacher_dir=args.teacher_dir,
        output_dir=args.output_dir,
        seed=args.seed,
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
        raise ValueError("Stage 3B.0 config must be a mapping")
    section = data.get("stage3b0_nonlearned_clustering_baselines", data)
    if not isinstance(section, dict):
        raise ValueError("Stage 3B.0 config section must be a mapping")
    return dict(section)


if __name__ == "__main__":
    main()
