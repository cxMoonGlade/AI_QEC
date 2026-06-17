from __future__ import annotations

import argparse
from collections.abc import Iterable
import json
from pathlib import Path
from typing import Any

import yaml

from scope_static.google.baseline_suite import BaselineSuiteConfig, run_google_d3d5_baseline_suite


DEFAULT_CONFIG = Path("configs/scope_static/google_d3d5_baselines.yaml")


def run_google_d3d5_baselines_from_config(
    *,
    config_path: str | Path | None = None,
    dataset_root: str | Path | None = None,
    output_dir: str | Path | None = None,
    max_leaves_per_distance_basis: int | None = None,
    max_shots_per_leaf: int | None = None,
    detector_limit: int | None = None,
    torch_epochs: int | None = None,
    seed: int | None = None,
    baseline_keys: str | None = None,
) -> dict[str, object]:
    cfg = _config_from_mapping(_load_config(Path(config_path) if config_path is not None else DEFAULT_CONFIG))
    if dataset_root is not None:
        cfg = _replace_config(cfg, dataset_root=Path(dataset_root))
    if output_dir is not None:
        cfg = _replace_config(cfg, output_dir=Path(output_dir))
    if max_leaves_per_distance_basis is not None:
        cfg = _replace_config(cfg, max_leaves_per_distance_basis=int(max_leaves_per_distance_basis))
    if max_shots_per_leaf is not None:
        cfg = _replace_config(cfg, max_shots_per_leaf=int(max_shots_per_leaf))
    if detector_limit is not None:
        cfg = _replace_config(cfg, detector_limit=int(detector_limit))
    if torch_epochs is not None:
        cfg = _replace_config(cfg, torch_epochs=int(torch_epochs))
    if seed is not None:
        cfg = _replace_config(cfg, seed=int(seed))
    if baseline_keys is not None:
        cfg = _replace_config(cfg, baseline_keys=_tuple_str(baseline_keys))
    return run_google_d3d5_baseline_suite(cfg)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    result = run_google_d3d5_baselines_from_config(
        config_path=args.config,
        dataset_root=args.dataset_root,
        output_dir=args.output_dir,
        max_leaves_per_distance_basis=args.max_leaves_per_distance_basis,
        max_shots_per_leaf=args.max_shots_per_leaf,
        detector_limit=args.detector_limit,
        torch_epochs=args.torch_epochs,
        seed=args.seed,
        baseline_keys=args.baseline_keys,
    )
    if args.progress_json:
        print(
            json.dumps(
                {
                    "decision": result.get("decision"),
                    "selected_leaf_count": dict(result.get("dataset", {})).get("selected_leaf_count"),
                    "wall_clock_seconds": result.get("wall_clock_seconds"),
                    "output_dir": dict(result.get("config", {})).get("output_dir"),
                    "uses_scope_layer123_or_v2_adapter": dict(result.get("claim_boundary", {})).get(
                        "uses_scope_layer123_or_v2_adapter"
                    ),
                },
                sort_keys=True,
            )
        )
    else:
        output_dir = dict(result.get("config", {})).get("output_dir")
        print("Google D3/D5 raw baseline suite complete")
        print(f"decision: {result.get('decision')}")
        print(f"selected_leaf_count: {dict(result.get('dataset', {})).get('selected_leaf_count')}")
        print(f"output_dir: {output_dir}")
        print(f"metrics: {Path(str(output_dir)) / 'metrics.json'}")
        print(f"summary: {Path(str(output_dir)) / 'summary.md'}")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run raw Google D3/D5 baselines, optionally including the SCOPE teacher-learner comparable adapter."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--dataset-root")
    parser.add_argument("--output-dir")
    parser.add_argument("--max-leaves-per-distance-basis", type=int)
    parser.add_argument("--max-shots-per-leaf", type=int)
    parser.add_argument("--detector-limit", type=int)
    parser.add_argument("--torch-epochs", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--baseline-keys")
    parser.add_argument("--progress-json", action="store_true")
    return parser.parse_args(argv)


def _load_config(config_path: Path | None) -> dict[str, Any]:
    if config_path is None or not Path(config_path).exists():
        return {}
    data = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Google D3/D5 baseline config must be a mapping")
    section = data.get("google_d3d5_baselines", data)
    if not isinstance(section, dict):
        raise ValueError("google_d3d5_baselines config section must be a mapping")
    return dict(section)


def _config_from_mapping(cfg: dict[str, Any]) -> BaselineSuiteConfig:
    default = BaselineSuiteConfig()
    return BaselineSuiteConfig(
        dataset_root=Path(cfg.get("dataset_root", default.dataset_root)),
        dataset_name=str(cfg.get("dataset_name", default.dataset_name)),
        output_dir=Path(cfg.get("output_dir", default.output_dir)),
        distances=_tuple_int_or_none(cfg.get("distances", default.distances)),
        bases=_tuple_str_or_none(cfg.get("bases", default.bases)),
        rounds=_tuple_int_or_none(cfg.get("rounds", default.rounds)),
        max_leaves_per_distance_basis=_optional_int(
            cfg.get("max_leaves_per_distance_basis", default.max_leaves_per_distance_basis)
        ),
        max_shots_per_leaf=_optional_int(cfg.get("max_shots_per_leaf", default.max_shots_per_leaf)),
        detector_limit=int(cfg.get("detector_limit", default.detector_limit)),
        train_fraction=float(cfg.get("train_fraction", default.train_fraction)),
        seed=int(cfg.get("seed", default.seed)),
        seeds=_tuple_int(cfg.get("seeds", default.seeds)),
        validation_fraction=float(cfg.get("validation_fraction", default.validation_fraction)),
        selection_profile=str(cfg.get("selection_profile", default.selection_profile)),
        mixture_components=int(cfg.get("mixture_components", default.mixture_components)),
        max_iter=int(cfg.get("max_iter", default.max_iter)),
        torch_epochs=int(cfg.get("torch_epochs", default.torch_epochs)),
        torch_batch_size=int(cfg.get("torch_batch_size", default.torch_batch_size)),
        gan_epochs=_optional_int(cfg.get("gan_epochs", default.gan_epochs)),
        rbm_steps=_optional_int(cfg.get("rbm_steps", default.rbm_steps)),
        autoregressive_steps=_optional_int(cfg.get("autoregressive_steps", default.autoregressive_steps)),
        external_repo_root=Path(cfg.get("external_repo_root", default.external_repo_root)),
        external_work_dir=Path(cfg.get("external_work_dir", default.external_work_dir)),
        qecgpt_network=str(cfg.get("qecgpt_network", default.qecgpt_network)),
        qecgpt_depth=int(cfg.get("qecgpt_depth", default.qecgpt_depth)),
        qecgpt_width=int(cfg.get("qecgpt_width", default.qecgpt_width)),
        qecgpt_d_model=int(cfg.get("qecgpt_d_model", default.qecgpt_d_model)),
        qecgpt_n_heads=int(cfg.get("qecgpt_n_heads", default.qecgpt_n_heads)),
        qecgpt_d_ff=int(cfg.get("qecgpt_d_ff", default.qecgpt_d_ff)),
        qecgpt_n_layers=int(cfg.get("qecgpt_n_layers", default.qecgpt_n_layers)),
        qecgpt_batch_size=int(cfg.get("qecgpt_batch_size", default.qecgpt_batch_size)),
        qecgpt_lr=float(cfg.get("qecgpt_lr", default.qecgpt_lr)),
        qecgpt_device=str(cfg.get("qecgpt_device", default.qecgpt_device)),
        rbm_hidden_units=_optional_int(cfg.get("rbm_hidden_units", default.rbm_hidden_units)),
        rbm_learning_rate=float(cfg.get("rbm_learning_rate", default.rbm_learning_rate)),
        checkpoint_every_leaf_results=_optional_int(
            cfg.get("checkpoint_every_leaf_results", default.checkpoint_every_leaf_results)
        ),
        baseline_keys=_tuple_str(cfg.get("baseline_keys", default.baseline_keys)),
    )


def _replace_config(cfg: BaselineSuiteConfig, **updates: object) -> BaselineSuiteConfig:
    data = cfg.__dict__.copy()
    data.update(updates)
    return BaselineSuiteConfig(**data)


def _tuple_int(value: object) -> tuple[int, ...]:
    if isinstance(value, str):
        return tuple(int(item.strip()) for item in value.split(",") if item.strip())
    if isinstance(value, Iterable):
        return tuple(int(item) for item in value)
    return (int(value),)


def _tuple_int_or_none(value: object) -> tuple[int, ...] | None:
    if value is None or value == "":
        return None
    return _tuple_int(value)


def _tuple_str(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return tuple(item.strip() for item in value.split(",") if item.strip())
    if isinstance(value, Iterable):
        return tuple(str(item) for item in value)
    return (str(value),)


def _tuple_str_or_none(value: object) -> tuple[str, ...] | None:
    if value is None or value == "":
        return None
    return _tuple_str(value)


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


if __name__ == "__main__":
    main()
