from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scope_static.mechanism_discovery.property_recovery import (
    DEFAULT_ASSIGNMENT_SOURCE,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PROPERTY_HEAD_MODEL,
    DEFAULT_STAGE3A5_DIR,
    DEFAULT_STAGE3A_DIR,
    DEFAULT_STAGE3B1_DIR,
    run_stage5b1_property_recovery,
)


def run_stage5b1_property_recovery_from_config(
    *,
    config_path: str | Path | None = None,
    stage3a_dir: str | Path | None = None,
    stage3a5_dir: str | Path | None = None,
    stage3b1_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    teacher_dir: str | Path | None = None,
    assignment_source: str | None = None,
    assignment_path: str | Path | None = None,
    assignment_key: str | None = None,
    property_head_model: str | None = None,
) -> dict[str, object]:
    cfg = _load_config(config_path)
    s3a = Path(stage3a_dir) if stage3a_dir is not None else Path(str(cfg.get("stage3a_dir", DEFAULT_STAGE3A_DIR)))
    s3a5 = Path(stage3a5_dir) if stage3a5_dir is not None else Path(str(cfg.get("stage3a5_dir", DEFAULT_STAGE3A5_DIR)))
    s3b1 = Path(stage3b1_dir) if stage3b1_dir is not None else Path(str(cfg.get("stage3b1_dir", DEFAULT_STAGE3B1_DIR)))
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", DEFAULT_OUTPUT_DIR)))
    result = run_stage5b1_property_recovery(
        stage3a_dir=s3a,
        stage3a5_dir=s3a5,
        stage3b1_dir=s3b1,
        output_dir=output,
        teacher_dir=None if teacher_dir is None and not cfg.get("teacher_dir") else Path(str(teacher_dir if teacher_dir is not None else cfg.get("teacher_dir"))),
        assignment_source=str(assignment_source if assignment_source is not None else cfg.get("assignment_source", DEFAULT_ASSIGNMENT_SOURCE)),
        assignment_path=assignment_path if assignment_path is not None else cfg.get("assignment_path"),
        assignment_key=str(assignment_key if assignment_key is not None else cfg.get("assignment_key")) if (assignment_key is not None or cfg.get("assignment_key") is not None) else None,
        property_head_model=str(property_head_model if property_head_model is not None else cfg.get("property_head_model", DEFAULT_PROPERTY_HEAD_MODEL)),
    )
    print(
        "Stage 5B1 property recovery complete\n"
        f"  decision={result.get('decision')}\n"
        f"  assignment_source={dict(result.get('assignment_source_audit', {})).get('assignment_source')}\n"
        f"  output={output}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run Stage 5B1 context-relative property recovery.")
    parser.add_argument("--config", type=Path, default=Path("configs/scope_static/stage5b1_property_recovery.yaml"))
    parser.add_argument("--stage3a-dir", type=Path)
    parser.add_argument("--stage3a5-dir", type=Path)
    parser.add_argument("--stage3b1-dir", type=Path)
    parser.add_argument("--teacher-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--assignment-source", default=None)
    parser.add_argument("--assignment-path", type=Path)
    parser.add_argument("--assignment-key", default=None)
    parser.add_argument("--property-head-model", default=None)
    args = parser.parse_args(argv)
    run_stage5b1_property_recovery_from_config(
        config_path=args.config,
        stage3a_dir=args.stage3a_dir,
        stage3a5_dir=args.stage3a5_dir,
        stage3b1_dir=args.stage3b1_dir,
        teacher_dir=args.teacher_dir,
        output_dir=args.output_dir,
        assignment_source=args.assignment_source,
        assignment_path=args.assignment_path,
        assignment_key=args.assignment_key,
        property_head_model=args.property_head_model,
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
        raise ValueError("Stage 5B1 config must be a mapping")
    section = data.get("stage5b1_property_recovery", data)
    if not isinstance(section, dict):
        raise ValueError("Stage 5B1 config section must be a mapping")
    return dict(section)


if __name__ == "__main__":
    main()
