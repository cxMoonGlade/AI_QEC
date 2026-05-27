from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from scope_static.experiments.s2d_config import load_s2d_physical_config, output_root_from_config
from scope_static.physical_oracle import run_physical_oracle_stack as _run_physical_oracle_stack


def run_physical_oracle_stack(
    config_path: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
    bootstrap_replicates: int | None = None,
    random_baseline_trials: int | None = None,
    run_local_inverse: str | None = None,
) -> dict[str, object]:
    physical_cfg = load_s2d_physical_config(config_path)
    stack_cfg = _load_stack_config(config_path)
    root = output_root_from_config(physical_cfg)
    output = Path(output_dir) if output_dir is not None else Path(str(stack_cfg.get("output_dir", root / "S2D_PHYSICAL_ORACLE_stack")))
    return _run_physical_oracle_stack(
        physical_cfg,
        output_dir=output,
        bootstrap_replicates=int(bootstrap_replicates if bootstrap_replicates is not None else stack_cfg.get("bootstrap_replicates", 16)),
        random_baseline_trials=int(random_baseline_trials if random_baseline_trials is not None else stack_cfg.get("random_baseline_trials", 64)),
        run_local_inverse=str(run_local_inverse if run_local_inverse is not None else stack_cfg.get("run_local_inverse", "auto")),
    )


def _load_stack_config(config_path: str | Path | None) -> dict[str, object]:
    if config_path is None:
        return {}
    data = yaml.safe_load(Path(config_path).read_text())
    if not isinstance(data, dict):
        raise ValueError("Physical Oracle Stack config must be a mapping")
    section = data.get("physical_oracle_stack", {})
    if section is None:
        return {}
    if not isinstance(section, dict):
        raise ValueError("physical_oracle_stack config must be a mapping")
    return dict(section)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the S2D Physical Oracle Stack.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--bootstrap-replicates", type=int, default=None)
    parser.add_argument("--random-baseline-trials", type=int, default=None)
    parser.add_argument("--run-local-inverse", choices=("auto", "always"), default=None)
    args = parser.parse_args(argv)
    result = run_physical_oracle_stack(
        args.config,
        output_dir=args.output_dir,
        bootstrap_replicates=args.bootstrap_replicates,
        random_baseline_trials=args.random_baseline_trials,
        run_local_inverse=args.run_local_inverse,
    )
    print(
        "Physical Oracle Stack complete\n"
        f"  diagnosis={result['verdicts']['overall_diagnosis']}\n"
        f"  output={result['output_dir']}"
    )
    print(json.dumps(result["verdicts"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
