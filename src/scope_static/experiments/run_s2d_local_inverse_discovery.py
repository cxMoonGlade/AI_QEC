from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scope_static.experiments.s2d_config import load_s2d_physical_config, output_root_from_config
from scope_static.physical.local_inverse import run_physical_local_inverse_discovery


def run_s2d_local_inverse_discovery(
    config_path: str | Path | None = None,
    *,
    teacher_dir: str | Path | None = None,
    separability_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, object]:
    physical_cfg = load_s2d_physical_config(config_path)
    local_cfg = _load_local_inverse_config(config_path)
    root = output_root_from_config(physical_cfg)
    teacher = Path(teacher_dir) if teacher_dir is not None else Path(str(local_cfg.get("teacher_dir", root / "S2D_PHYS1_teacher")))
    separability = (
        Path(separability_dir)
        if separability_dir is not None
        else Path(str(local_cfg.get("separability_dir", root / "S2D_PHYS2_oracle_separability")))
    )
    output = (
        Path(output_dir)
        if output_dir is not None
        else Path(str(local_cfg.get("output_dir", root / "S2D_PHYS3_local_inverse")))
    )
    cfg = dict(physical_cfg)
    cfg.update(local_cfg)
    result = run_physical_local_inverse_discovery(
        teacher_dir=teacher,
        separability_dir=separability,
        output_dir=output,
        config=cfg,
    )
    print(
        "S2D PHYS3 local inverse discovery complete\n"
        f"  result={result.get('s2d3_result')}\n"
        f"  local_inverse ARI={float(result['main_result']['ari']):.4f} NMI={float(result['main_result']['nmi']):.4f}\n"
        f"  direct S/alpha ARI={float(result['direct_S_alpha_result']['ari']):.4f} "
        f"NMI={float(result['direct_S_alpha_result']['nmi']):.4f}\n"
        f"  output={output}"
    )
    return result


def _load_local_inverse_config(config_path: str | Path | None) -> dict[str, object]:
    if config_path is None:
        return {}
    data = yaml.safe_load(Path(config_path).read_text())
    if not isinstance(data, dict):
        raise ValueError("S2D local inverse config must be a mapping")
    section = data.get("s2d_local_inverse", {})
    if section is None:
        return {}
    if not isinstance(section, dict):
        raise ValueError("s2d_local_inverse config must be a mapping")
    return dict(section)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run S2D PHYS3 physical local-inverse mechanism discovery.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--teacher-dir", type=Path, default=None)
    parser.add_argument("--separability-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    run_s2d_local_inverse_discovery(
        args.config,
        teacher_dir=args.teacher_dir,
        separability_dir=args.separability_dir,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
