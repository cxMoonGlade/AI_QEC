from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scope_static.learner import run_phyc3c_validation_audit


def run_phyc3c_validation_from_config(
    *,
    config_path: str | Path | None = None,
    teacher_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, object]:
    cfg = _load_config(config_path)
    source = Path(teacher_dir) if teacher_dir is not None else Path(str(cfg.get("teacher_dir", "")))
    if not str(source):
        raise ValueError("teacher_dir is required")
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", "outputs/scope_static/PHYC3c_validation_robustness")))
    result = run_phyc3c_validation_audit(
        teacher_dir=source,
        output_dir=output,
        shots=int(cfg.get("shots", 20_000)),
        seeds=tuple(int(value) for value in cfg.get("seeds", [29])),
        sampling_modes=tuple(str(value) for value in cfg.get("sampling_modes", ["expected"])),
        robustness_modes=tuple(bool(value) for value in cfg.get("robustness_modes", [False])),
        batch_sizes=tuple(int(value) for value in cfg.get("batch_sizes", [3, 5, 6])),
        shrinkage_alphas=tuple(float(value) for value in cfg.get("shrinkage_alphas", [0.0, 0.25, 0.5])),
        ridge=float(cfg.get("ridge", 1e-6)),
        variance_floor=float(cfg.get("variance_floor", 1e-8)),
        max_pca_components_values=tuple(int(value) for value in cfg.get("max_pca_components_values", [8, 24])),
        primary_head=str(cfg.get("primary_head", "PHYC3c_diagonal_gaussian")),
        grid_heads=tuple(str(value) for value in cfg.get("grid_heads", ["PHYC3c_diagonal_gaussian"])),
        primary_min_ba=float(cfg.get("primary_min_ba", 1.0)),
        primary_min_nmi=float(cfg.get("primary_min_nmi", 1.0)),
        primary_min_m13_recall=float(cfg.get("primary_min_m13_recall", 1.0)),
        required_m13_contexts=int(cfg.get("required_m13_contexts", 2)),
    )
    print(
        "PHYC3c validation complete\n"
        f"  decision={result.get('decision')}\n"
        f"  robustness_passed={bool(result.get('robustness_passed'))}\n"
        f"  non_leakage_passed={bool(result.get('non_leakage_passed'))}\n"
        f"  protocol_validity_passed={bool(result.get('protocol_validity_passed'))}\n"
        f"  primary_min_BA={float(result.get('primary_min_BA', 0.0)):.4f}\n"
        f"  primary_min_NMI={float(result.get('primary_min_NMI', 0.0)):.4f}\n"
        f"  primary_min_M13_recall={float(result.get('primary_min_M13_recall', 0.0)):.4f}\n"
        f"  output={output}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run PHYC3c robustness, non-leakage, and protocol validation.")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--teacher-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    run_phyc3c_validation_from_config(config_path=args.config, teacher_dir=args.teacher_dir, output_dir=args.output_dir)


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
        raise ValueError("PHYC3c validation config must be a mapping")
    section = data.get("phyc3c_validation", data)
    if not isinstance(section, dict):
        raise ValueError("PHYC3c validation config section must be a mapping")
    return dict(section)


if __name__ == "__main__":
    main()
