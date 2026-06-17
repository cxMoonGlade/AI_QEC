from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scope_static.learner import run_phyc3_no_leakage_learner_recovery


def run_phyc3_no_leakage_learner_recovery_experiment(
    *,
    teacher_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    contract: str | None = None,
    theta: float | None = None,
    ridge: float | None = None,
    seed: int | None = None,
    config_path: str | Path | None = None,
) -> dict[str, object]:
    cfg = _load_config(config_path)
    source = Path(teacher_dir) if teacher_dir is not None else Path(str(cfg.get("teacher_dir", "")))
    if not str(source):
        raise ValueError("teacher_dir is required")
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", "outputs/scope_static/PHYC3_no_leakage_learner_recovery")))
    result = run_phyc3_no_leakage_learner_recovery(
        teacher_dir=source,
        output_dir=output,
        contract_variant=str(contract if contract is not None else cfg.get("contract", "balanced")),
        theta=float(theta if theta is not None else cfg.get("theta", 0.18)),
        ridge=float(ridge if ridge is not None else cfg.get("ridge", 1e-8)),
        seed=int(seed if seed is not None else cfg.get("seed", 0)),
    )
    print(
        "Layer 3 no-leakage learner recovery complete (legacy PHYC3)\n"
        f"  contract={result.get('contract_variant')}\n"
        f"  decision={result.get('decision')}\n"
        f"  passed={bool(result.get('contract_passed'))}\n"
        f"  learner_BA={float(result.get('balanced_accuracy', 0.0)):.4f}\n"
        f"  learner_ARI={float(result.get('adjusted_rand_index', 0.0)):.4f}\n"
        f"  learner_NMI={float(result.get('normalized_mutual_info', 0.0)):.4f}\n"
        f"  teacher_self_predictions_allowed={bool(result.get('teacher_self_predictions_allowed', False))}\n"
        f"  output={output}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run Layer 3 no-leakage sampled-observation learner recovery.")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--teacher-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--contract", choices=("balanced", "weighted"))
    parser.add_argument("--theta", type=float)
    parser.add_argument("--ridge", type=float)
    parser.add_argument("--seed", type=int)
    args = parser.parse_args(argv)
    run_phyc3_no_leakage_learner_recovery_experiment(
        config_path=args.config,
        teacher_dir=args.teacher_dir,
        output_dir=args.output_dir,
        contract=args.contract,
        theta=args.theta,
        ridge=args.ridge,
        seed=args.seed,
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
        raise ValueError("Layer 3 learner recovery config must be a mapping")
    section = data.get("layer3_no_leakage_learner_recovery", data.get("phyc3_no_leakage_learner_recovery", data))
    if not isinstance(section, dict):
        raise ValueError("Layer 3 learner recovery config section must be a mapping")
    return dict(section)


if __name__ == "__main__":
    main()
