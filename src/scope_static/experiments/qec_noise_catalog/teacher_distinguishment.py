from __future__ import annotations

import argparse
from pathlib import Path

from scope_static.teacher import run_sampled_observation_separability_audit


def run_teacher_distinguishment(
    *,
    teacher_dir: str | Path,
    output_dir: str | Path,
    contract: str = "balanced",
    theta: float = 0.18,
    ridge: float = 1e-8,
    seed: int = 0,
) -> dict[str, object]:
    result = run_sampled_observation_separability_audit(
        teacher_dir=teacher_dir,
        output_dir=output_dir,
        contract_variant=contract,
        theta=float(theta),
        ridge=float(ridge),
        seed=int(seed),
    )
    print(
        "Layer 2 teacher self-audit complete\n"
        f"  contract={result.get('contract_variant')}\n"
        f"  decision={result.get('decision')}\n"
        f"  passed={bool(result.get('contract_passed'))}\n"
        f"  teacher_self_balanced_accuracy={float(result.get('balanced_accuracy', 0.0)):.4f}\n"
        f"  teacher_self_ari={float(result.get('adjusted_rand_index', 0.0)):.4f}\n"
        f"  teacher_self_nmi={float(result.get('normalized_mutual_info', 0.0)):.4f}\n"
        f"  learner_grouped_predictions_emitted={bool(result.get('phyc2_emits_learner_grouped_predictions', False))}\n"
        f"  learner_recovery_stage={result.get('learner_recovery_stage', 'PHYC3_no_leakage_learner_recovery')}\n"
        f"  output={output_dir}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run Layer 2 teacher self-audit only.")
    parser.add_argument("--teacher-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--contract", choices=("balanced", "weighted"), default="balanced")
    parser.add_argument("--theta", type=float, default=0.18)
    parser.add_argument("--ridge", type=float, default=1e-8)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)
    run_teacher_distinguishment(
        teacher_dir=args.teacher_dir,
        output_dir=args.output_dir,
        contract=args.contract,
        theta=args.theta,
        ridge=args.ridge,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
