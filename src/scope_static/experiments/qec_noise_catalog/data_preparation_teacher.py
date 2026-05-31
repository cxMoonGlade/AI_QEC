from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scope_static.data_preparation import (
    DEFAULT_LAYER1P_TEACHER_OUTPUT_DIR,
    generate_layer1p_teacher_dataset,
)


def run_data_preparation_teacher_from_config(
    *,
    config_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    audit_output_dir: str | Path | None = None,
) -> dict[str, object]:
    cfg = _load_config(config_path)
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", DEFAULT_LAYER1P_TEACHER_OUTPUT_DIR)))
    audit_output = (
        Path(audit_output_dir)
        if audit_output_dir is not None
        else (None if not cfg.get("audit_output_dir") else Path(str(cfg.get("audit_output_dir"))))
    )
    teacher_cfg = _teacher_config(cfg)
    result = generate_layer1p_teacher_dataset(
        teacher_cfg,
        output_dir=output,
        audit_output_dir=audit_output,
        tolerance_mode=str(cfg.get("tolerance_mode", "strict")),
        probability_tolerance=float(cfg.get("probability_tolerance", 1.0e-12)),
        random_state_count=int(cfg.get("random_state_count", 4)),
        enforce_pre_sampling_contract=bool(cfg.get("enforce_pre_sampling_contract", True)),
        enforce_post_sampling_physicality=bool(cfg.get("enforce_post_sampling_physicality", True)),
    )
    contract = dict(result.get("layer1p_teacher_contract", {}))
    print(
        "Layer1.P teacher generation complete\n"
        f"  decision={result.get('decision')}\n"
        f"  mechanisms={contract.get('num_mechanisms')}\n"
        f"  total_failures={contract.get('total_failures')}\n"
        f"  output={output}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate a Layer1.P physical-process teacher dataset.")
    parser.add_argument("--config", type=Path, default=Path("configs/scope_static/data_preparation_teacher.yaml"))
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--audit-output-dir", type=Path)
    args = parser.parse_args(argv)
    run_data_preparation_teacher_from_config(
        config_path=args.config,
        output_dir=args.output_dir,
        audit_output_dir=args.audit_output_dir,
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
        raise ValueError("Layer1.P teacher config must be a mapping")
    section = data.get("data_preparation_teacher", data.get("layer1p_teacher", data.get("s2d_physical", data)))
    if not isinstance(section, dict):
        raise ValueError("Layer1.P teacher config section must be a mapping")
    return dict(section)


def _teacher_config(cfg: dict[str, object]) -> dict[str, object]:
    if isinstance(cfg.get("teacher_config"), dict):
        return dict(cfg["teacher_config"])  # type: ignore[arg-type]
    runner_keys = {
        "name",
        "output_dir",
        "audit_output_dir",
        "tolerance_mode",
        "probability_tolerance",
        "random_state_count",
        "enforce_pre_sampling_contract",
        "enforce_post_sampling_physicality",
    }
    return {str(key): value for key, value in cfg.items() if str(key) not in runner_keys}


if __name__ == "__main__":
    main()


run_layer1p_teacher_from_config = run_data_preparation_teacher_from_config
