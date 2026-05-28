from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scope_static.experiments.s2d_config import load_s2d_physical_config, output_root_from_config
from scope_static.physical.local_observable_teacher import generate_local_observable_teacher_dataset


def run_local_observable_gpu_teacher(
    config_path: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
    run_name: str | None = None,
    shots: int | None = None,
    balanced_min_instances_per_mechanism: int | None = None,
    disable_slot_remap: bool = False,
) -> dict[str, object]:
    physical_cfg = load_s2d_physical_config(config_path)
    full_cfg = _load_config(config_path)
    selected_run = _selected_run(full_cfg, run_name=run_name)
    cfg = dict(physical_cfg)
    cfg.update({key: value for key, value in selected_run.items() if key not in {"name", "purpose", "enabled", "secondary_stress"}})
    typed_cfg = full_cfg.get("s2d11_typed_spam_gate_invariant_learner", {})
    if isinstance(typed_cfg, dict):
        cfg.update(dict(typed_cfg.get("physical_overrides", {})))
        cfg["probe_set"] = str(typed_cfg.get("tomography_probe_set", cfg.get("probe_set", "rzz_local_tomography")))
    cfg["backend"] = "local_observable_gpu"
    if shots is not None:
        cfg["shots"] = int(shots)
    if balanced_min_instances_per_mechanism is not None:
        cfg["balanced_min_instances_per_mechanism"] = int(balanced_min_instances_per_mechanism)
    if disable_slot_remap:
        cfg["local_observable_slot_remap"] = False

    root = output_root_from_config(physical_cfg)
    default_name = str(selected_run.get("name", "local_observable_gpu_teacher"))
    teacher_output = Path(output_dir) if output_dir is not None else root / f"{default_name}_local_observable_gpu" / "S2D_PHYS1_teacher"
    result = generate_local_observable_teacher_dataset(cfg, output_dir=teacher_output)
    sampling = result.get("sampling", {})
    if not isinstance(sampling, dict):
        sampling = {}
    print(
        "Local-observable GPU PHYS1 teacher complete\n"
        f"  output={teacher_output}\n"
        f"  mechanisms={result.get('mechanism_counts')}\n"
        f"  sampling_seconds={float(sampling.get('sampling_wall_clock_seconds', 0.0)):.6f}\n"
        f"  total_seconds={float(sampling.get('total_wall_clock_seconds', 0.0)):.6f}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate a PHYS1 sampled-observation teacher using Torch CUDA local responses.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--run-name", type=str, default=None)
    parser.add_argument("--shots", type=int, default=None)
    parser.add_argument("--balanced-min-instances-per-mechanism", type=int, default=None)
    parser.add_argument("--disable-slot-remap", action="store_true", help="Run PHYC2.no_slot_remap_ablation by preserving original local-observable qubit cells.")
    args = parser.parse_args(argv)
    run_local_observable_gpu_teacher(
        args.config,
        output_dir=args.output_dir,
        run_name=args.run_name,
        shots=args.shots,
        balanced_min_instances_per_mechanism=args.balanced_min_instances_per_mechanism,
        disable_slot_remap=bool(args.disable_slot_remap),
    )


def _load_config(config_path: str | Path | None) -> dict[str, object]:
    if config_path is None:
        return {}
    data = yaml.safe_load(Path(config_path).read_text())
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("config must be a mapping")
    return dict(data)


def _selected_run(config: dict[str, object], *, run_name: str | None) -> dict[str, object]:
    section = config.get("s2d11_typed_spam_gate_invariant_learner", {})
    if not isinstance(section, dict):
        return {}
    runs = section.get("runs", [])
    if not isinstance(runs, list):
        return {}
    candidates = [dict(item) for item in runs if isinstance(item, dict) and item.get("enabled", True)]
    if not candidates:
        return {}
    if run_name is None:
        return dict(candidates[0])
    for item in candidates:
        if str(item.get("name", "")) == str(run_name):
            return dict(item)
    names = ", ".join(str(item.get("name", "")) for item in candidates)
    raise ValueError(f"unknown run name {run_name!r}; available runs: {names}")


if __name__ == "__main__":
    main()
