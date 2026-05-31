from __future__ import annotations

import argparse
from pathlib import Path

from scope_static.experiments.qec_noise_catalog.config import load_s2d_physical_config, output_root_from_config
from scope_static.teacher.separability import run_oracle_separability_audit


def run_s2d_oracle_separability(
    config_path: str | Path | None = None,
    *,
    teacher_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, object]:
    cfg = load_s2d_physical_config(config_path)
    root = output_root_from_config(cfg)
    teacher = Path(teacher_dir) if teacher_dir is not None else root / "S2D_PHYS1_teacher"
    output = Path(output_dir) if output_dir is not None else root / "S2D_PHYS2_oracle_separability"
    result = run_oracle_separability_audit(
        teacher_dir=teacher,
        output_dir=output,
        paper_informed=bool(cfg.get("paper_informed_ptm_features", True)),
    )
    print(
        "S2D PHYS2 oracle separability complete\n"
        f"  gate={result.get('separability_gate')} ari={float(result.get('ari', 0.0)):.4f} nmi={float(result.get('nmi', 0.0)):.4f}\n"
        f"  output={output}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run S2D PHYS2 oracle separability audit.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--teacher-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    run_s2d_oracle_separability(args.config, teacher_dir=args.teacher_dir, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
