from __future__ import annotations

import argparse
from pathlib import Path

from scope_static.experiments.s2d_config import load_s2d_physical_config, output_root_from_config
from scope_static.physical.teacher import generate_physical_teacher_dataset


def run_s2d_physical_teacher(
    config_path: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
    preflight_dir: str | Path | None = None,
) -> dict[str, object]:
    cfg = load_s2d_physical_config(config_path)
    root = output_root_from_config(cfg)
    teacher_output = Path(output_dir) if output_dir is not None else root / "S2D_PHYS1_teacher"
    preflight_output = Path(preflight_dir) if preflight_dir is not None else root / "S2D_PHYS0_preflight"
    result = generate_physical_teacher_dataset(cfg, output_dir=teacher_output, preflight_dir=preflight_output)
    print(
        "Layer 1 data preparation complete (legacy S2D PHYS1/PHYC1 teacher)\n"
        f"  output={teacher_output}\n"
        f"  mechanisms={result.get('mechanism_counts')}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate the Layer 1 Data Preparation physical-oracle teacher dataset.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--preflight-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    run_s2d_physical_teacher(args.config, output_dir=args.output_dir, preflight_dir=args.preflight_dir)


if __name__ == "__main__":
    main()
