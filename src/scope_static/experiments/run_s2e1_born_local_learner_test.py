from __future__ import annotations

import argparse
from pathlib import Path

from scope_static.physical.s2e1_born_local_learner_test import run_s2e1_born_local_learner_test as _run


def run_s2e1_born_local_learner_test(
    *,
    teacher_dir: str | Path,
    phyc2_dir: str | Path,
    output_dir: str | Path,
    contract: str = "balanced",
    require_full_scope: bool = True,
    source_model: str = "born_local",
) -> dict[str, object]:
    result = _run(
        teacher_dir=teacher_dir,
        phyc2_dir=phyc2_dir,
        output_dir=output_dir,
        contract_variant=contract,
        require_full_scope=bool(require_full_scope),
        expected_response_model=str(source_model),
    )
    print(
        "S2E.1 Born-local learner test complete\n"
        f"  decision={result.get('decision')}\n"
        f"  passed={bool(result.get('contract_passed'))}\n"
        f"  source_model={result.get('expected_response_model')}\n"
        f"  phyc2={phyc2_dir}\n"
        f"  output={output_dir}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the S2E.1 Born-local learner test from existing PHYC2 data.")
    parser.add_argument("--teacher-dir", type=Path, required=True)
    parser.add_argument("--phyc2-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--contract", choices=("balanced", "weighted"), default="balanced")
    parser.add_argument("--source-model", type=str, default="born_local", help="Expected local_observable_response_model, e.g. born_local or separability_v2.")
    parser.add_argument("--allow-partial-scope", action="store_true")
    args = parser.parse_args(argv)
    run_s2e1_born_local_learner_test(
        teacher_dir=args.teacher_dir,
        phyc2_dir=args.phyc2_dir,
        output_dir=args.output_dir,
        contract=args.contract,
        require_full_scope=not bool(args.allow_partial_scope),
        source_model=args.source_model,
    )


if __name__ == "__main__":
    main()
