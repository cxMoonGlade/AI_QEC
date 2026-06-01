from __future__ import annotations

import argparse
from collections.abc import Iterable as IterableABC
import json
from pathlib import Path
from typing import Any, Iterable

import yaml

from scope_static.google.s3_visible_surface import (
    DEFAULT_DATASET_NAME,
    DEFAULT_DATASET_ROOT,
    DEFAULT_SPLIT_POLICY,
)
from scope_static.google.s3_visible_surface_v2 import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REGION_FAMILIES,
    DEFAULT_ROUND_BANDS,
    write_google_s3_visible_surface_v2,
)


DEFAULT_CONFIG = Path("configs/scope_static/google_s3_visible_adapter_v2.yaml")


def run_google_s3_visible_adapter_v2_from_config(
    *,
    config_path: str | Path | None = None,
    dataset_root: str | Path | None = None,
    output_dir: str | Path | None = None,
    cache_dir: str | Path | None = None,
    max_contexts: int | None = None,
    round_bands: Iterable[str] | None = None,
    region_families: Iterable[str] | None = None,
    shotblocks_per_context: int | None = None,
    shotblock_size: int | None = None,
    max_shots_per_context: int | None = None,
) -> dict[str, object]:
    cfg = _load_config(Path(config_path) if config_path is not None else DEFAULT_CONFIG)
    result = write_google_s3_visible_surface_v2(
        dataset_root=dataset_root if dataset_root is not None else cfg.get("dataset_root", DEFAULT_DATASET_ROOT),
        dataset_name=str(cfg.get("dataset_name", DEFAULT_DATASET_NAME)),
        output_dir=output_dir if output_dir is not None else cfg.get("output_dir", DEFAULT_OUTPUT_DIR),
        cache_dir=cache_dir if cache_dir is not None else cfg.get("cache_dir"),
        dem_source=str(cfg.get("dem_source", "decoder_si1000")),
        max_contexts=int(max_contexts if max_contexts is not None else cfg.get("max_contexts", 24)),
        round_bands=tuple(round_bands) if round_bands is not None else tuple(cfg.get("round_bands", DEFAULT_ROUND_BANDS)),
        region_families=(
            tuple(region_families) if region_families is not None else tuple(cfg.get("region_families", DEFAULT_REGION_FAMILIES))
        ),
        shotblocks_per_context=int(
            shotblocks_per_context if shotblocks_per_context is not None else cfg.get("shotblocks_per_context", 8)
        ),
        shotblock_size=int(shotblock_size if shotblock_size is not None else cfg.get("shotblock_size", 4096)),
        min_shotblock_size=_optional_int(cfg.get("min_shotblock_size")),
        max_shots_per_context=_optional_int(
            max_shots_per_context if max_shots_per_context is not None else cfg.get("max_shots_per_context")
        ),
        basis=_optional_str(cfg.get("basis")),
        distance=_optional_int(cfg.get("distance")),
        rounds=_optional_int(cfg.get("rounds")),
        seed=int(cfg.get("seed", 0)),
        split_policy=str(cfg.get("split_policy", DEFAULT_SPLIT_POLICY)),
    )
    print("Google S3 visible adapter V2 complete")
    print(f"decision: {result.get('decision')}")
    print(f"output: {result.get('output_dir')}")
    return result


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    cfg = _load_config(args.config)
    result = write_google_s3_visible_surface_v2(
        dataset_root=args.dataset_root or cfg.get("dataset_root", DEFAULT_DATASET_ROOT),
        dataset_name=str(args.dataset_name or cfg.get("dataset_name", DEFAULT_DATASET_NAME)),
        output_dir=args.output_dir or cfg.get("output_dir", DEFAULT_OUTPUT_DIR),
        cache_dir=args.cache_dir if args.cache_dir is not None else cfg.get("cache_dir"),
        dem_source=str(args.dem_source or cfg.get("dem_source", "decoder_si1000")),
        max_contexts=int(args.max_contexts if args.max_contexts is not None else cfg.get("max_contexts", 24)),
        round_bands=_csv_or_config(args.round_bands, cfg.get("round_bands", DEFAULT_ROUND_BANDS)),
        region_families=_csv_or_config(args.region_families, cfg.get("region_families", DEFAULT_REGION_FAMILIES)),
        shotblocks_per_context=int(
            args.shotblocks_per_context if args.shotblocks_per_context is not None else cfg.get("shotblocks_per_context", 8)
        ),
        shotblock_size=int(args.shotblock_size if args.shotblock_size is not None else cfg.get("shotblock_size", 4096)),
        min_shotblock_size=_optional_int(
            args.min_shotblock_size if args.min_shotblock_size is not None else cfg.get("min_shotblock_size")
        ),
        max_shots_per_context=_optional_int(
            args.max_shots_per_context if args.max_shots_per_context is not None else cfg.get("max_shots_per_context")
        ),
        basis=args.basis if args.basis is not None else _optional_str(cfg.get("basis")),
        distance=_optional_int(args.distance if args.distance is not None else cfg.get("distance")),
        rounds=_optional_int(args.rounds if args.rounds is not None else cfg.get("rounds")),
        seed=int(args.seed if args.seed is not None else cfg.get("seed", 0)),
        split_policy=str(args.split_policy or cfg.get("split_policy", DEFAULT_SPLIT_POLICY)),
    )
    if args.progress_json:
        print(
            json.dumps(
                {
                    "decision": result.get("decision"),
                    "output_dir": result.get("output_dir"),
                    "record_count": dict(result.get("visible_feature_matrix", {})).get("record_count"),
                    "feature_count": dict(result.get("visible_feature_matrix", {})).get("feature_count"),
                    "adequacy_passed": dict(result.get("adequacy_report", {})).get("passed"),
                },
                sort_keys=True,
            )
        )
    else:
        print("Google S3 visible adapter V2 complete")
        print(f"decision: {result.get('decision')}")
        print(f"output: {result.get('output_dir')}")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Google real-data Stage 3 V2 public syndrome-response signature artifacts.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--dataset-root")
    parser.add_argument("--dataset-name")
    parser.add_argument("--output-dir")
    parser.add_argument("--cache-dir")
    parser.add_argument("--dem-source")
    parser.add_argument("--max-contexts", type=int)
    parser.add_argument("--round-bands", help="Comma-separated round bands, e.g. early,mid,late")
    parser.add_argument("--region-families", help="Comma-separated public region families")
    parser.add_argument("--shotblocks-per-context", type=int)
    parser.add_argument("--shotblock-size", type=int)
    parser.add_argument("--min-shotblock-size", type=int)
    parser.add_argument("--max-shots-per-context", type=int)
    parser.add_argument("--basis")
    parser.add_argument("--distance", type=int)
    parser.add_argument("--rounds", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--split-policy")
    parser.add_argument("--progress-json", action="store_true")
    return parser.parse_args(argv)


def _load_config(config_path: Path | None) -> dict[str, Any]:
    if config_path is None or not Path(config_path).exists():
        return {}
    data = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Google S3 visible adapter V2 config must be a mapping")
    section = data.get("google_s3_visible_adapter_v2", data.get("google_s3_visible_adapter", data))
    if not isinstance(section, dict):
        raise ValueError("google_s3_visible_adapter_v2 config section must be a mapping")
    return dict(section)


def _csv_or_config(value: str | None, fallback: object) -> tuple[str, ...]:
    if value is not None:
        return tuple(item.strip() for item in str(value).split(",") if item.strip())
    if isinstance(fallback, str):
        return tuple(item.strip() for item in fallback.split(",") if item.strip())
    if isinstance(fallback, IterableABC):
        return tuple(str(item) for item in fallback)
    return ()


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _optional_str(value: object) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


if __name__ == "__main__":
    main()
