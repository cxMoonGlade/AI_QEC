from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scope_static.physical.stage3a_protocol_freeze import (
    DEFAULT_ASSIGNMENT_UNIT,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SPLIT_POLICY,
    run_stage3a_dataset_protocol_freeze,
)


def run_stage3a_protocol_freeze_from_config(
    *,
    config_path: str | Path | None = None,
    teacher_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    shots: int | None = None,
    seed: int | None = None,
    batch_size: int | None = None,
    assignment_unit: str | None = None,
) -> dict[str, object]:
    cfg = _load_config(config_path)
    source = Path(teacher_dir) if teacher_dir is not None else Path(str(cfg.get("teacher_dir", "")))
    if not str(source):
        raise ValueError("teacher_dir is required")
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", DEFAULT_OUTPUT_DIR)))
    result = run_stage3a_dataset_protocol_freeze(
        teacher_dir=source,
        output_dir=output,
        shots=int(shots if shots is not None else cfg.get("shots", 20_000)),
        seed=int(seed if seed is not None else cfg.get("seed", 0)),
        robustness_mode=bool(cfg.get("robustness_mode", False)),
        sampling_mode=str(cfg.get("sampling_mode", "expected")),
        batch_size=int(batch_size if batch_size is not None else cfg.get("batch_size", 5)),
        assignment_unit=str(assignment_unit if assignment_unit is not None else cfg.get("assignment_unit", DEFAULT_ASSIGNMENT_UNIT)),
        split_policy=str(cfg.get("split_policy", DEFAULT_SPLIT_POLICY)),
    )
    acceptance = dict(result.get("acceptance_audit", {}))
    print(
        "Stage 3A dataset/protocol freeze complete\n"
        f"  decision={result.get('decision')}\n"
        f"  passed={bool(acceptance.get('passed', False))}\n"
        f"  assignment_unit={dict(result.get('assignment_unit', {})).get('j_definition')}\n"
        f"  output={output}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run Stage 3A dataset and protocol freeze.")
    parser.add_argument("--config", type=Path, default=Path("configs/scope_static/stage3a_protocol_freeze.yaml"))
    parser.add_argument("--teacher-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--shots", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--assignment-unit")
    args = parser.parse_args(argv)
    run_stage3a_protocol_freeze_from_config(
        config_path=args.config,
        teacher_dir=args.teacher_dir,
        output_dir=args.output_dir,
        shots=args.shots,
        seed=args.seed,
        batch_size=args.batch_size,
        assignment_unit=args.assignment_unit,
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
        raise ValueError("Stage 3A config must be a mapping")
    section = data.get("stage3a_protocol_freeze", data)
    if not isinstance(section, dict):
        raise ValueError("Stage 3A config section must be a mapping")
    return dict(section)


if __name__ == "__main__":
    main()
