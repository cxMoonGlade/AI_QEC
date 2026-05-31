from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scope_static.learner import run_phyc3b_zx_visible_alias_breaking_probe_suite


def run_phyc3b_zx_visible_alias_breaking_probe_suite_from_config(
    *,
    config_path: str | Path | None = None,
    teacher_dir: str | Path | None = None,
    phyc2_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    shots: int | None = None,
    seed: int | None = None,
    robustness_mode: bool | None = None,
    sampling_mode: str | None = None,
) -> dict[str, object]:
    cfg = _load_config(config_path)
    source = Path(teacher_dir) if teacher_dir is not None else Path(str(cfg.get("teacher_dir", "")))
    if not str(source):
        raise ValueError("teacher_dir is required")
    phyc2_value = phyc2_dir if phyc2_dir is not None else cfg.get("phyc2_dir")
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", "outputs/scope_static/PHYC3b_ZX_visible_alias_breaking_probe_suite")))
    result = run_phyc3b_zx_visible_alias_breaking_probe_suite(
        teacher_dir=source,
        phyc2_dir=None if phyc2_value in {None, ""} else Path(str(phyc2_value)),
        output_dir=output,
        shots=int(shots if shots is not None else cfg.get("shots", 20_000)),
        seed=int(seed if seed is not None else cfg.get("seed", 0)),
        robustness_mode=bool(robustness_mode if robustness_mode is not None else cfg.get("robustness_mode", False)),
        sampling_mode=str(sampling_mode if sampling_mode is not None else cfg.get("sampling_mode", "expected")),
        signature_decimals=int(cfg.get("signature_decimals", 10)),
    )
    print(
        "PHYC3b Z/X visible alias-breaking probe suite complete\n"
        f"  decision={result.get('decision')}\n"
        f"  ceiling_BA_before={float(result.get('deterministic_ceiling_BA_before', 0.0)):.4f}\n"
        f"  ceiling_BA_after={float(result.get('deterministic_ceiling_BA_after', 0.0)):.4f}\n"
        f"  ceiling_NMI_before={float(result.get('deterministic_ceiling_NMI_before', 0.0)):.4f}\n"
        f"  ceiling_NMI_after={float(result.get('deterministic_ceiling_NMI_after', 0.0)):.4f}\n"
        f"  learner_NMI={float(result.get('learner_NMI', 0.0)):.4f}\n"
        f"  incompatible_predictions={int(result.get('incompatible_prediction_count', 0))}\n"
        f"  output={output}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run PHYC3b Z/X-only visible alias-breaking probe suite.")
    parser.add_argument("--config", type=Path, default=Path("configs/scope_static/phyc3b_zx_visible_alias_breaking_probe_suite.yaml"))
    parser.add_argument("--teacher-dir", type=Path)
    parser.add_argument("--phyc2-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--shots", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--sampling-mode", choices=["expected", "multinomial"])
    parser.add_argument("--robustness-mode", action="store_true")
    args = parser.parse_args(argv)
    run_phyc3b_zx_visible_alias_breaking_probe_suite_from_config(
        config_path=args.config,
        teacher_dir=args.teacher_dir,
        phyc2_dir=args.phyc2_dir,
        output_dir=args.output_dir,
        shots=args.shots,
        seed=args.seed,
        robustness_mode=True if args.robustness_mode else None,
        sampling_mode=args.sampling_mode,
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
        raise ValueError("PHYC3b config must be a mapping")
    section = data.get("phyc3b_zx_visible_alias_breaking_probe_suite", data)
    if not isinstance(section, dict):
        raise ValueError("PHYC3b config section must be a mapping")
    return dict(section)


if __name__ == "__main__":
    main()
