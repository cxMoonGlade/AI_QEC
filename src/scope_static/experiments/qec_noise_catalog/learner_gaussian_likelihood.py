from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scope_static.learner import run_phyc3c_distributional_gaussian_likelihood_head


def run_phyc3c_distributional_gaussian_likelihood_from_config(
    *,
    config_path: str | Path | None = None,
    teacher_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    batch_size: int | None = None,
    seed: int | None = None,
) -> dict[str, object]:
    cfg = _load_config(config_path)
    source = Path(teacher_dir) if teacher_dir is not None else Path(str(cfg.get("teacher_dir", "")))
    if not str(source):
        raise ValueError("teacher_dir is required")
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", "outputs/scope_static/PHYC3c_distributional_gaussian_likelihood_head")))
    result = run_phyc3c_distributional_gaussian_likelihood_head(
        teacher_dir=source,
        output_dir=output,
        shots=int(cfg.get("shots", 20_000)),
        seed=int(seed if seed is not None else cfg.get("seed", 0)),
        robustness_mode=bool(cfg.get("robustness_mode", False)),
        sampling_mode=str(cfg.get("sampling_mode", "expected")),
        batch_size=int(batch_size if batch_size is not None else cfg.get("batch_size", 5)),
        shrinkage_alpha=float(cfg.get("shrinkage_alpha", 0.25)),
        ridge=float(cfg.get("ridge", 1e-6)),
        variance_floor=float(cfg.get("variance_floor", 1e-8)),
        max_pca_components=int(cfg.get("max_pca_components", 24)),
    )
    print(
        "PHYC3c distributional Gaussian likelihood head complete\n"
        f"  decision={result.get('decision')}\n"
        f"  primary_head={result.get('primary_head')}\n"
        f"  primary_mode={result.get('primary_mode')}\n"
        f"  learner_BA={float(result.get('learner_BA', 0.0)):.4f}\n"
        f"  learner_NMI={float(result.get('learner_NMI', 0.0)):.4f}\n"
        f"  m13_recall={float(result.get('m13_recall', 0.0)):.4f}\n"
        f"  output={output}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run PHYC3c distributional Gaussian likelihood learner head.")
    parser.add_argument("--config", type=Path, default=Path("configs/scope_static/phyc3c_distributional_gaussian_likelihood.yaml"))
    parser.add_argument("--teacher-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--seed", type=int)
    args = parser.parse_args(argv)
    run_phyc3c_distributional_gaussian_likelihood_from_config(
        config_path=args.config,
        teacher_dir=args.teacher_dir,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
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
        raise ValueError("PHYC3c config must be a mapping")
    section = data.get("phyc3c_distributional_gaussian_likelihood", data)
    if not isinstance(section, dict):
        raise ValueError("PHYC3c config section must be a mapping")
    return dict(section)


if __name__ == "__main__":
    main()
