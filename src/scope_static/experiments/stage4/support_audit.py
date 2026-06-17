from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from scope_static.mechanism_discovery.support_audit import DEFAULT_OUTPUT_DIR, run_stage4_support_alignment_audit


DEFAULT_CONFIG = Path("configs/scope_static/stage4_support_audit_v1.yaml")


def run_stage4_support_audit_from_config(
    *,
    config_path: str | Path | None = None,
    stage4_source_dir: str | Path | None = None,
    google_stage3a_dir: str | Path | None = None,
    source_pretrain_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, object]:
    cfg = _load_config(config_path)
    source = Path(stage4_source_dir if stage4_source_dir is not None else str(cfg.get("stage4_source_dir", "")))
    google = Path(google_stage3a_dir if google_stage3a_dir is not None else str(cfg.get("google_stage3a_dir", "")))
    pretrain_value = source_pretrain_dir if source_pretrain_dir is not None else cfg.get("source_pretrain_dir")
    if not str(source) or not str(google):
        raise ValueError("stage4 support audit requires stage4_source_dir and google_stage3a_dir")
    result = run_stage4_support_alignment_audit(
        stage4_source_dir=source,
        google_stage3a_dir=google,
        source_pretrain_dir=pretrain_value,
        output_dir=output_dir if output_dir is not None else cfg.get("output_dir", DEFAULT_OUTPUT_DIR),
    )
    print("S4 support alignment audit complete")
    print(f"decision={result.get('decision')}")
    print(f"output={result.get('output_dir')}")
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run S4 source/Google support alignment audit.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--stage4-source-dir", type=Path)
    parser.add_argument("--google-stage3a-dir", type=Path)
    parser.add_argument("--source-pretrain-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    run_stage4_support_audit_from_config(
        config_path=args.config,
        stage4_source_dir=args.stage4_source_dir,
        google_stage3a_dir=args.google_stage3a_dir,
        source_pretrain_dir=args.source_pretrain_dir,
        output_dir=args.output_dir,
    )


def _load_config(path: str | Path | None) -> dict[str, Any]:
    if path is None or not Path(path).exists():
        return {}
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Stage 4 support audit config must be a mapping")
    section = data.get("stage4_support_audit_v1", data)
    if not isinstance(section, dict):
        raise ValueError("stage4_support_audit_v1 config section must be a mapping")
    return dict(section)


if __name__ == "__main__":
    main()
