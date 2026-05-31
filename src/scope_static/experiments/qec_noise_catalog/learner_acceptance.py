from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scope_static.learner import run_phyc3_canonical_acceptance


def run_learner_acceptance_from_config(
    *,
    config_path: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, object]:
    cfg = _load_config(config_path)
    output = (
        Path(output_dir)
        if output_dir is not None
        else Path(str(cfg.get("output_dir", "outputs/scope_static/PHYC3_canonical_quality_acceptance")))
    )
    result = run_phyc3_canonical_acceptance(
        phyc2_dir=Path(str(cfg["phyc2_dir"])),
        phyc3a_dir=Path(str(cfg["phyc3a_dir"])),
        phyc3b_dir=Path(str(cfg["phyc3b_dir"])),
        phyc3c_dir=Path(str(cfg["phyc3c_dir"])),
        phyc3c_validation_dir=Path(str(cfg["phyc3c_validation_dir"])),
        teacher_dir=None if not cfg.get("teacher_dir") else Path(str(cfg["teacher_dir"])),
        output_dir=output,
        primary_head=str(cfg.get("primary_head", "PHYC3c_diagonal_gaussian")),
        max_mean_predicted_channel_distance=float(cfg.get("max_mean_predicted_channel_distance", 0.02)),
        max_worst_predicted_channel_distance=float(cfg.get("max_worst_predicted_channel_distance", 0.005)),
    )
    print(
        "Layer 3 canonical quality acceptance complete (legacy PHYC3)\n"
        f"  decision={result.get('decision')}\n"
        f"  passed={bool(result.get('contract_passed'))}\n"
        f"  canonical_source={dict(result.get('canonical_prediction_source', {})).get('source_name', 'unknown')}\n"
        f"  incompatible_predictions={int(dict(result.get('canonical_quality_metrics', {})).get('incompatible_prediction_count', 0))}\n"
        f"  output={output}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run Layer 3 canonical quality acceptance resolver.")
    parser.add_argument("--config", type=Path, default=Path("configs/scope_static/learner_acceptance.yaml"))
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    run_learner_acceptance_from_config(config_path=args.config, output_dir=args.output_dir)


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
        raise ValueError("Learner acceptance config must be a mapping")
    section = data.get(
        "learner_acceptance",
        data.get(
            "learner_canonical_acceptance",
            data.get("layer3_canonical_acceptance", data.get("phyc3_canonical_acceptance", data)),
        ),
    )
    if not isinstance(section, dict):
        raise ValueError("Learner acceptance config section must be a mapping")
    return dict(section)


if __name__ == "__main__":
    main()


run_learner_canonical_acceptance_from_config = run_learner_acceptance_from_config
run_phyc3_canonical_acceptance_from_config = run_learner_acceptance_from_config
