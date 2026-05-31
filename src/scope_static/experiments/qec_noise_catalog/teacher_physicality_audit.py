from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scope_static.data_preparation import DEFAULT_PHYSICALITY_AUDIT_OUTPUT_DIR
from scope_static.data_preparation import run_teacher_physicality_audit


def run_teacher_physicality_audit_from_config(
    *,
    config_path: str | Path | None = None,
    teacher_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    tolerance_mode: str | None = None,
) -> dict[str, object]:
    cfg = _load_config(config_path)
    teacher = Path(teacher_dir) if teacher_dir is not None else Path(str(cfg.get("teacher_dir", "")))
    if not str(teacher):
        raise ValueError("teacher_dir is required")
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", DEFAULT_PHYSICALITY_AUDIT_OUTPUT_DIR)))
    result = run_teacher_physicality_audit(
        teacher_dir=teacher,
        output_dir=output,
        tolerance_mode=str(tolerance_mode if tolerance_mode is not None else cfg.get("tolerance_mode", "strict")),
        tolerance=None if cfg.get("tolerance") is None else float(cfg["tolerance"]),
        probability_tolerance=float(cfg.get("probability_tolerance", 1.0e-12)),
        random_state_count=int(cfg.get("random_state_count", 4)),
    )
    summary = dict(result.get("summary", {}))
    print(
        "Layer1.P teacher physicality audit complete\n"
        f"  decision={result.get('decision')}\n"
        f"  teacher_physicality_passed={summary.get('teacher_physicality_passed')}\n"
        f"  total_failures={summary.get('total_failures')}\n"
        f"  output={output}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run Layer1.P teacher CPTP/POVM physicality audit.")
    parser.add_argument("--config", type=Path, default=Path("configs/scope_static/teacher_physicality_audit.yaml"))
    parser.add_argument("--teacher-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--tolerance-mode", type=str)
    args = parser.parse_args(argv)
    run_teacher_physicality_audit_from_config(
        config_path=args.config,
        teacher_dir=args.teacher_dir,
        output_dir=args.output_dir,
        tolerance_mode=args.tolerance_mode,
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
        raise ValueError("teacher physicality audit config must be a mapping")
    section = data.get("teacher_physicality_audit", data)
    if not isinstance(section, dict):
        raise ValueError("teacher physicality audit config section must be a mapping")
    return dict(section)


if __name__ == "__main__":
    main()
