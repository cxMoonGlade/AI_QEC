from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scope_static.mechanism_discovery.observability_ceiling import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A5_DIR
from scope_static.mechanism_discovery.protocol_freeze import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A_DIR
from scope_static.mechanism_discovery.discovery_model import (
    DEFAULT_COMPLEXITY_PENALTY,
    DEFAULT_FINAL_TEMPERATURE,
    DEFAULT_INITIAL_TEMPERATURE,
    DEFAULT_CONTEXT_BALANCE_PENALTY,
    DEFAULT_MAX_CV_FOLDS,
    DEFAULT_MAX_ITER,
    DEFAULT_OPERATION_CONTEXT_WEIGHT,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SEED,
    EVALUATOR_MODE_CONTROLLED_CATALOG,
    run_stage3b1_first_discovery_model,
)


def run_stage3b1_discovery_model_from_config(
    *,
    config_path: str | Path | None = None,
    stage3a_dir: str | Path | None = None,
    stage3a5_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    teacher_dir: str | Path | None = None,
    seed: int | None = None,
    context_balance_penalty: float | None = None,
    operation_context_weight: float | None = None,
    evaluator_mode: str | None = None,
    k_values: list[int] | None = None,
) -> dict[str, object]:
    cfg = _load_config(config_path)
    s3a = Path(stage3a_dir) if stage3a_dir is not None else Path(str(cfg.get("stage3a_dir", DEFAULT_STAGE3A_DIR)))
    s3a5 = Path(stage3a5_dir) if stage3a5_dir is not None else Path(str(cfg.get("stage3a5_dir", DEFAULT_STAGE3A5_DIR)))
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", DEFAULT_OUTPUT_DIR)))
    result = run_stage3b1_first_discovery_model(
        stage3a_dir=s3a,
        stage3a5_dir=s3a5,
        output_dir=output,
        teacher_dir=None if teacher_dir is None and not cfg.get("teacher_dir") else Path(str(teacher_dir if teacher_dir is not None else cfg.get("teacher_dir"))),
        seed=int(seed if seed is not None else cfg.get("seed", DEFAULT_SEED)),
        max_iter=int(cfg.get("max_iter", DEFAULT_MAX_ITER)),
        initial_temperature=float(cfg.get("initial_temperature", DEFAULT_INITIAL_TEMPERATURE)),
        final_temperature=float(cfg.get("final_temperature", DEFAULT_FINAL_TEMPERATURE)),
        complexity_penalty=float(cfg.get("complexity_penalty", DEFAULT_COMPLEXITY_PENALTY)),
        max_cv_folds=None if cfg.get("max_cv_folds") is None else int(cfg.get("max_cv_folds", DEFAULT_MAX_CV_FOLDS)),
        context_balance_penalty=float(context_balance_penalty if context_balance_penalty is not None else cfg.get("context_balance_penalty", DEFAULT_CONTEXT_BALANCE_PENALTY)),
        operation_context_weight=float(
            operation_context_weight if operation_context_weight is not None else cfg.get("operation_context_weight", DEFAULT_OPERATION_CONTEXT_WEIGHT)
        ),
        evaluator_mode=str(evaluator_mode if evaluator_mode is not None else cfg.get("evaluator_mode", EVALUATOR_MODE_CONTROLLED_CATALOG)),
        k_values=k_values if k_values is not None else _int_list(cfg.get("k_values")),
    )
    summary = dict(result.get("learned_assignment_summary", {}))
    print(
        "Stage 3B.1 first discovery model complete\n"
        f"  decision={result.get('decision')}\n"
        f"  selected_k_mode={summary.get('selected_k_mode')}\n"
        f"  selected_k={summary.get('selected_k')}\n"
        f"  output={output}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run Stage 3B.1 visible-only prototype-mixture discovery model.")
    parser.add_argument("--config", type=Path, default=Path("configs/scope_static/stage3b1_discovery_model.yaml"))
    parser.add_argument("--stage3a-dir", type=Path)
    parser.add_argument("--stage3a5-dir", type=Path)
    parser.add_argument("--teacher-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--context-balance-penalty", type=float)
    parser.add_argument("--operation-context-weight", type=float)
    parser.add_argument("--evaluator-mode", default=None)
    parser.add_argument("--k-values", default=None)
    args = parser.parse_args(argv)
    run_stage3b1_discovery_model_from_config(
        config_path=args.config,
        stage3a_dir=args.stage3a_dir,
        stage3a5_dir=args.stage3a5_dir,
        teacher_dir=args.teacher_dir,
        output_dir=args.output_dir,
        seed=args.seed,
        context_balance_penalty=args.context_balance_penalty,
        operation_context_weight=args.operation_context_weight,
        evaluator_mode=args.evaluator_mode,
        k_values=_csv_ints(args.k_values),
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
        raise ValueError("Stage 3B.1 config must be a mapping")
    section = data.get("stage3b1_first_discovery_model", data)
    if not isinstance(section, dict):
        raise ValueError("Stage 3B.1 config section must be a mapping")
    return dict(section)


def _csv_ints(value: str | None) -> list[int] | None:
    if value is None or not str(value).strip():
        return None
    return [int(item.strip()) for item in str(value).split(",") if item.strip()]


def _int_list(value: object) -> list[int] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return _csv_ints(value)
    if isinstance(value, list):
        return [int(item) for item in value]
    return [int(value)]


if __name__ == "__main__":
    main()
