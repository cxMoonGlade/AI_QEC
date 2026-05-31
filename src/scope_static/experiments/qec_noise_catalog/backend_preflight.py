from __future__ import annotations

import argparse
from pathlib import Path

from scope_static.experiments.qec_noise_catalog.config import load_s2d_physical_config, output_root_from_config
from scope_static.primitives.preflight import audit_cudaq_backend, write_backend_audit


def run_backend_preflight(
    config_path: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
) -> dict[str, object]:
    cfg = load_s2d_physical_config(config_path)
    output = Path(output_dir) if output_dir is not None else output_root_from_config(cfg) / "S2D_PHYS0_preflight"
    audit = audit_cudaq_backend(
        backend=str(cfg.get("backend", "cudaq")),
        require_gpu=bool(cfg.get("require_gpu", True)),
        cudaq_target=str(cfg.get("cudaq_target", "nvidia")),
        cudaq_target_options=str(cfg.get("cudaq_target_options", "fp32")),
    )
    write_backend_audit(audit, output)
    print(format_preflight_terminal_summary(audit, output))
    return audit


def format_preflight_terminal_summary(audit: dict[str, object], output: Path) -> str:
    return (
        "S2D PHYS0 preflight complete\n"
        f"  status={audit.get('status')} backend_usable={audit.get('backend_usable')}\n"
        f"  audit={output / 'backend_audit.json'}"
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run S2D PHYS0 CUDA-Q backend preflight.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when the backend audit fails.")
    args = parser.parse_args(argv)
    audit = run_backend_preflight(args.config, output_dir=args.output_dir)
    if args.strict and not bool(audit.get("backend_usable")):
        raise SystemExit(1)


if __name__ == "__main__":
    main()


run_s2d_preflight = run_backend_preflight
