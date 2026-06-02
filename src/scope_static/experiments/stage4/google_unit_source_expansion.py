from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from scope_static.mechanism_discovery.google_unit_source import (
    DEFAULT_OUTPUT_DIR,
    run_stage4_google_unit_source_expansion,
)


DEFAULT_CONFIG = Path("configs/scope_static/stage4_google_unit_source_expansion_v1.yaml")


def run_stage4_google_unit_source_expansion_from_config(
    *,
    config_path: str | Path | None = None,
    teacher_dir: str | Path | None = None,
    google_stage3a_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, object]:
    cfg = _load_config(config_path)
    teacher = Path(teacher_dir if teacher_dir is not None else str(cfg.get("teacher_dir", "")))
    google = Path(google_stage3a_dir if google_stage3a_dir is not None else str(cfg.get("google_stage3a_dir", "")))
    if not str(teacher) or not str(google):
        raise ValueError("stage4 Google-unit source expansion requires teacher_dir and google_stage3a_dir")
    result = run_stage4_google_unit_source_expansion(
        teacher_dir=teacher,
        google_stage3a_dir=google,
        output_dir=output_dir if output_dir is not None else cfg.get("output_dir", DEFAULT_OUTPUT_DIR),
        assignment_geometry_dir=cfg.get("assignment_geometry_dir"),
        source_pretrain_dir=cfg.get("source_pretrain_dir"),
        seed=int(cfg.get("seed", 0)),
        k=int(cfg.get("k", 32)),
        shotblock_size=int(cfg.get("shotblock_size", 16)),
        max_source_shots_per_record=cfg.get("max_source_shots_per_record"),
        mixture_component_count=int(cfg.get("mixture_component_count", 3)),
        design_fraction=float(cfg.get("design_fraction", 0.50)),
        validation_fraction=float(cfg.get("validation_fraction", 0.25)),
        min_missing_mode_mass=float(cfg.get("min_missing_mode_mass", 0.02)),
    )
    print("S4.6 Google-unit source expansion complete")
    print(f"decision={result.get('decision')}")
    print(f"output={result.get('output_dir')}")
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run S4.6 Google-unit controlled source expansion.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--teacher-dir", type=Path)
    parser.add_argument("--google-stage3a-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    run_stage4_google_unit_source_expansion_from_config(
        config_path=args.config,
        teacher_dir=args.teacher_dir,
        google_stage3a_dir=args.google_stage3a_dir,
        output_dir=args.output_dir,
    )


def _load_config(path: str | Path | None) -> dict[str, Any]:
    if path is None or not Path(path).exists():
        return {}
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Stage 4 Google-unit source expansion config must be a mapping")
    section = data.get("stage4_google_unit_source_expansion_v1", data)
    if not isinstance(section, dict):
        raise ValueError("stage4_google_unit_source_expansion_v1 config section must be a mapping")
    return dict(section)


if __name__ == "__main__":
    main()
