from __future__ import annotations

import argparse
from pathlib import Path

from .property_recovery import run_stage5b1_property_recovery_from_config


DEFAULT_CONFIG = Path("configs/scope_static/stage5b1b_conditional_property_recovery.yaml")


def run_stage5b1b_conditional_property_recovery_from_config(
    *,
    config_path: str | Path | None = DEFAULT_CONFIG,
    stage3a_dir: str | Path | None = None,
    stage3a5_dir: str | Path | None = None,
    stage3b1_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    teacher_dir: str | Path | None = None,
    assignment_source: str | None = None,
    assignment_path: str | Path | None = None,
    assignment_key: str | None = None,
) -> dict[str, object]:
    return run_stage5b1_property_recovery_from_config(
        config_path=config_path,
        stage3a_dir=stage3a_dir,
        stage3a5_dir=stage3a5_dir,
        stage3b1_dir=stage3b1_dir,
        output_dir=output_dir,
        teacher_dir=teacher_dir,
        assignment_source=assignment_source,
        assignment_path=assignment_path,
        assignment_key=assignment_key,
        property_head_model="conditional_visible_context_property_head",
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run Stage 5B1b conditional visible-only property recovery.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--stage3a-dir", type=Path)
    parser.add_argument("--stage3a5-dir", type=Path)
    parser.add_argument("--stage3b1-dir", type=Path)
    parser.add_argument("--teacher-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--assignment-source", default=None)
    parser.add_argument("--assignment-path", type=Path)
    parser.add_argument("--assignment-key", default=None)
    args = parser.parse_args(argv)
    run_stage5b1b_conditional_property_recovery_from_config(
        config_path=args.config,
        stage3a_dir=args.stage3a_dir,
        stage3a5_dir=args.stage3a5_dir,
        stage3b1_dir=args.stage3b1_dir,
        teacher_dir=args.teacher_dir,
        output_dir=args.output_dir,
        assignment_source=args.assignment_source,
        assignment_path=args.assignment_path,
        assignment_key=args.assignment_key,
    )


if __name__ == "__main__":
    main()
