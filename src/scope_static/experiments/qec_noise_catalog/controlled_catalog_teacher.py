from __future__ import annotations

import argparse
from pathlib import Path

from scope_static.experiments.qec_noise_catalog.config import load_s2d_physical_config, output_root_from_config
from scope_static.data_preparation import generate_layer1p_teacher_dataset
from scope_static.primitives.preflight import audit_cudaq_backend, write_backend_audit


def generate_controlled_catalog_teacher_dataset(
    config: dict[str, object] | None = None,
    *,
    output_dir: str | Path,
    preflight_dir: str | Path,
) -> dict[str, object]:
    """Compatibility wrapper: public Layer 1 generation now uses Layer1.P."""

    cfg = dict(config or {})
    audit = audit_cudaq_backend(
        backend=str(cfg.get("backend", "cudaq")),
        require_gpu=bool(cfg.get("require_gpu", True)),
        cudaq_target=str(cfg.get("cudaq_target", "nvidia")),
        cudaq_target_options=str(cfg.get("cudaq_target_options", "fp32")),
    )
    write_backend_audit(audit, preflight_dir)
    if not bool(audit.get("backend_usable", False)):
        raise RuntimeError("Layer1.P requires a passing CUDA-Q backend preflight")
    cfg["backend"] = "cudaq"
    result = generate_layer1p_teacher_dataset(cfg, output_dir=output_dir)
    result["backend_audit_dir"] = str(preflight_dir)
    result["cudaq_backend"] = {
        "target": audit.get("cudaq_target"),
        "gpu_count": audit.get("cudaq_gpu_count"),
        "tiny_cudaq_sample": audit.get("tiny_cudaq_sample"),
    }
    return result


def run_controlled_catalog_teacher(
    config_path: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
    preflight_dir: str | Path | None = None,
) -> dict[str, object]:
    cfg = load_s2d_physical_config(config_path)
    root = output_root_from_config(cfg)
    teacher_output = Path(output_dir) if output_dir is not None else root / "Layer1P_teacher"
    preflight_output = Path(preflight_dir) if preflight_dir is not None else root / "S2D_PHYS0_preflight"
    result = generate_controlled_catalog_teacher_dataset(cfg, output_dir=teacher_output, preflight_dir=preflight_output)
    print(
        "Layer1.P data preparation complete\n"
        f"  output={teacher_output}\n"
        f"  mechanisms={dict(result.get('layer1p_teacher_contract', {})).get('num_mechanisms')}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate the controlled-catalog data-preparation teacher dataset.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--preflight-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    run_controlled_catalog_teacher(args.config, output_dir=args.output_dir, preflight_dir=args.preflight_dir)


if __name__ == "__main__":
    main()


generate_physical_teacher_dataset = generate_controlled_catalog_teacher_dataset
run_s2d_physical_teacher = run_controlled_catalog_teacher
