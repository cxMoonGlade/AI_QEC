from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from scope_static.google.s4_bridge_surface import DEFAULT_OUTPUT_DIR, write_stage4_synthetic_google_shaped_freeze


DEFAULT_CONFIG = Path("configs/scope_static/stage4_synthetic_google_surface_v1.yaml")


def run_stage4_synthetic_freeze_from_config(
    *,
    config_path: str | Path | None = None,
    teacher_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    google_stage3a_dir: str | Path | None = None,
) -> dict[str, object]:
    cfg = _load_config(config_path)
    teacher = Path(teacher_dir if teacher_dir is not None else str(cfg.get("teacher_dir", "")))
    if not str(teacher):
        raise ValueError("stage4 synthetic freeze requires teacher_dir")
    result = write_stage4_synthetic_google_shaped_freeze(
        teacher_dir=teacher,
        output_dir=output_dir if output_dir is not None else cfg.get("output_dir", DEFAULT_OUTPUT_DIR),
        google_stage3a_dir=google_stage3a_dir if google_stage3a_dir is not None else cfg.get("google_stage3a_dir"),
        round_bands=tuple(cfg.get("round_bands", ("all",))),
        region_families=tuple(cfg.get("region_families", ("full_patch",))),
        split_policy=str(cfg.get("split_policy", "leave_one_context_group_out")),
        dataset_family=str(cfg.get("dataset_family", "synthetic_controlled_catalog")),
        basis=str(cfg.get("basis", "X")),
        distance=_optional_int(cfg.get("distance")),
        rounds=_optional_int(cfg.get("rounds")),
        shotblock_size=int(cfg.get("shotblock_size", 16)),
        max_source_shots_per_record=_optional_int(cfg.get("max_source_shots_per_record")),
        mirror_public_context_from_google_v2=bool(cfg.get("mirror_public_context_from_google_v2", False)),
        max_mirrored_public_contexts=_optional_int(cfg.get("max_mirrored_public_contexts")),
        emit_context_rows=bool(cfg.get("emit_context_rows", False)),
        align_visible_feature_marginals_to_google_v2=bool(cfg.get("align_visible_feature_marginals_to_google_v2", False)),
        seed=int(cfg.get("seed", 0)),
    )
    print("S4.0 synthetic Google-shaped freeze complete")
    print(f"decision={result.get('decision')}")
    print(f"output={result.get('output_dir')}")
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run S4.0 synthetic Google-shaped bridge freeze.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--teacher-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--google-stage3a-dir", type=Path)
    args = parser.parse_args(argv)
    run_stage4_synthetic_freeze_from_config(
        config_path=args.config,
        teacher_dir=args.teacher_dir,
        output_dir=args.output_dir,
        google_stage3a_dir=args.google_stage3a_dir,
    )


def _load_config(path: str | Path | None) -> dict[str, Any]:
    if path is None or not Path(path).exists():
        return {}
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Stage 4 synthetic freeze config must be a mapping")
    section = data.get("stage4_synthetic_google_surface_v1", data)
    if not isinstance(section, dict):
        raise ValueError("stage4_synthetic_google_surface_v1 config section must be a mapping")
    return dict(section)


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


if __name__ == "__main__":
    main()
