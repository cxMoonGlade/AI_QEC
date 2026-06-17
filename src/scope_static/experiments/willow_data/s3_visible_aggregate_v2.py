from __future__ import annotations

import argparse
from collections.abc import Iterable as IterableABC
import json
from pathlib import Path
from typing import Any

import yaml

from scope_static.google.s3_visible_cache_v2 import (
    DEFAULT_CACHE_DIR,
    DEFAULT_REGION_FAMILIES,
    DEFAULT_ROUND_BANDS,
)
from scope_static.google.s3_visible_surface_v2 import write_google_s3_visible_aggregate_cache_v2


DEFAULT_CONFIG = Path("configs/scope_static/google_s3_visible_aggregate_v2.yaml")


def run_google_s3_visible_aggregate_v2_from_config(
    *,
    config_path: str | Path | None = None,
    cache_dir: str | Path | None = None,
    max_contexts: int | None = None,
    num_workers: int | None = None,
) -> dict[str, object]:
    cfg = _load_config(Path(config_path) if config_path is not None else DEFAULT_CONFIG)
    result = write_google_s3_visible_aggregate_cache_v2(
        cache_dir=cache_dir if cache_dir is not None else cfg.get("cache_dir", DEFAULT_CACHE_DIR),
        round_bands=tuple(cfg.get("round_bands", DEFAULT_ROUND_BANDS)),
        region_families=tuple(cfg.get("region_families", DEFAULT_REGION_FAMILIES)),
        max_contexts=max_contexts if max_contexts is not None else _optional_int(cfg.get("max_contexts")),
        num_workers=num_workers if num_workers is not None else _optional_int(cfg.get("num_workers")),
    )
    print("Google S3 visible aggregate V2 complete")
    print(f"decision: {result.get('decision')}")
    print(f"slowest_block: {result.get('slowest_block')}")
    return result


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    cfg = _load_config(args.config)
    result = write_google_s3_visible_aggregate_cache_v2(
        cache_dir=args.cache_dir or cfg.get("cache_dir", DEFAULT_CACHE_DIR),
        round_bands=_csv_or_config(args.round_bands, cfg.get("round_bands", DEFAULT_ROUND_BANDS)),
        region_families=_csv_or_config(args.region_families, cfg.get("region_families", DEFAULT_REGION_FAMILIES)),
        max_contexts=args.max_contexts if args.max_contexts is not None else _optional_int(cfg.get("max_contexts")),
        num_workers=args.num_workers if args.num_workers is not None else _optional_int(cfg.get("num_workers")),
    )
    if args.progress_json:
        print(
            json.dumps(
                {
                    "decision": result.get("decision"),
                    "context_count": result.get("context_count"),
                    "unit_count": result.get("unit_count"),
                    "slowest_block": result.get("slowest_block"),
                    "total_wallclock_seconds": result.get("total_wallclock_seconds"),
                    "num_workers": result.get("num_workers"),
                    "cache_dir": str(args.cache_dir or cfg.get("cache_dir", DEFAULT_CACHE_DIR)),
                },
                sort_keys=True,
            )
        )
    else:
        print("Google S3 visible aggregate V2 complete")
        print(f"decision: {result.get('decision')}")
        print(f"slowest_block: {result.get('slowest_block')}")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Precompute accelerated Google S3A V2 aggregate signature rows.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--cache-dir")
    parser.add_argument("--round-bands")
    parser.add_argument("--region-families")
    parser.add_argument("--max-contexts", type=int)
    parser.add_argument("--num-workers", type=int)
    parser.add_argument("--progress-json", action="store_true")
    return parser.parse_args(argv)


def _load_config(config_path: Path | None) -> dict[str, Any]:
    if config_path is None or not Path(config_path).exists():
        return {}
    data = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Google S3 visible aggregate V2 config must be a mapping")
    section = data.get("google_s3_visible_aggregate_v2", data)
    if not isinstance(section, dict):
        raise ValueError("google_s3_visible_aggregate_v2 config section must be a mapping")
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


if __name__ == "__main__":
    main()
