from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scope_static.mechanism_discovery.observability_ceiling import (
    DEFAULT_DISTANCE_THRESHOLD,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SIGNATURE_DECIMALS,
    run_stage3a5_observability_alias_ceiling,
)
from scope_static.mechanism_discovery.protocol_freeze import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A_DIR


def run_stage3a5_observability_ceiling_from_config(
    *,
    config_path: str | Path | None = None,
    stage3a_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    teacher_dir: str | Path | None = None,
    distance_threshold: float | None = None,
    signature_decimals: int | None = None,
) -> dict[str, object]:
    cfg = _load_config(config_path)
    s3a = Path(stage3a_dir) if stage3a_dir is not None else Path(str(cfg.get("stage3a_dir", DEFAULT_STAGE3A_DIR)))
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", DEFAULT_OUTPUT_DIR)))
    result = run_stage3a5_observability_alias_ceiling(
        stage3a_dir=s3a,
        output_dir=output,
        teacher_dir=None if teacher_dir is None and not cfg.get("teacher_dir") else Path(str(teacher_dir if teacher_dir is not None else cfg.get("teacher_dir"))),
        distance_threshold=float(distance_threshold if distance_threshold is not None else cfg.get("distance_threshold", DEFAULT_DISTANCE_THRESHOLD)),
        signature_decimals=int(signature_decimals if signature_decimals is not None else cfg.get("signature_decimals", DEFAULT_SIGNATURE_DECIMALS)),
    )
    alias = dict(result.get("oracle_alias_classes", {}))
    print(
        "Stage 3A.5 observability/alias ceiling complete\n"
        f"  decision={result.get('decision')}\n"
        f"  alias_classes={int(alias.get('alias_class_count', 0))}\n"
        f"  exact_label_claim_allowed={bool(alias.get('exact_label_recovery_claim_allowed', False))}\n"
        f"  output={output}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run Stage 3A.5 observability and alias ceiling audit.")
    parser.add_argument("--config", type=Path, default=Path("configs/scope_static/stage3a5_observability_ceiling.yaml"))
    parser.add_argument("--stage3a-dir", type=Path)
    parser.add_argument("--teacher-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--distance-threshold", type=float)
    parser.add_argument("--signature-decimals", type=int)
    args = parser.parse_args(argv)
    run_stage3a5_observability_ceiling_from_config(
        config_path=args.config,
        stage3a_dir=args.stage3a_dir,
        teacher_dir=args.teacher_dir,
        output_dir=args.output_dir,
        distance_threshold=args.distance_threshold,
        signature_decimals=args.signature_decimals,
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
        raise ValueError("Stage 3A.5 config must be a mapping")
    section = data.get("stage3a5_observability_alias_ceiling", data)
    if not isinstance(section, dict):
        raise ValueError("Stage 3A.5 config section must be a mapping")
    return dict(section)


if __name__ == "__main__":
    main()
