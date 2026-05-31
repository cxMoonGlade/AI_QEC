from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time

from scope_static.google.inventory import (
    DATASET_105Q,
    DATASET_REPETITION_D29,
    DATASET_SURFACE_SET1,
    DATASET_SURFACE_SET2,
    DEFAULT_DATASET_ROOTS,
    write_google_inventory_artifacts,
)


def main(argv: list[str] | None = None) -> dict[str, object]:
    start = time.perf_counter()
    args = _parse_args(argv)
    dataset_roots = {
        DATASET_REPETITION_D29: args.repetition_root,
        DATASET_SURFACE_SET1: args.set1_root,
        DATASET_SURFACE_SET2: args.set2_root,
        DATASET_105Q: args.surface_105q_root,
    }
    dataset_names = _csv(args.datasets)
    result = write_google_inventory_artifacts(
        output_dir=args.output_dir,
        dataset_roots=dataset_roots,
        dataset_names=dataset_names,
        dem_proxy_mode=args.dem_proxy_mode,
    )
    result["run"] = {
        "name": "Google_unified_preprocessing_inventory",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_names": dataset_names,
        "dem_proxy_mode": args.dem_proxy_mode,
        "read_only_source_datasets": True,
        "wall_seconds": time.perf_counter() - start,
    }
    run_path = Path(args.output_dir) / "run_manifest.json"
    run_path.write_text(json.dumps(_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.progress_json:
        print(json.dumps({"run_manifest_path": str(run_path), **_summary(result)}, sort_keys=True))
    else:
        print("Google unified preprocessing inventory complete")
        print(f"contexts: {result['num_contexts']} decoder_rows: {result['num_decoder_rows']}")
        print(f"context_manifest: {result['context_manifest_path']}")
        print(f"decoder_manifest: {result['decoder_manifest_path']}")
        print(f"audit: {result['audit_path']}")
    return result


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate read-only Google dataset inventory manifests.")
    parser.add_argument(
        "--datasets",
        default=",".join((DATASET_REPETITION_D29, DATASET_SURFACE_SET1, DATASET_SURFACE_SET2, DATASET_105Q)),
        help="Comma-separated Google dataset names to inventory.",
    )
    parser.add_argument("--repetition-root", default=str(DEFAULT_DATASET_ROOTS[DATASET_REPETITION_D29]))
    parser.add_argument("--set1-root", default=str(DEFAULT_DATASET_ROOTS[DATASET_SURFACE_SET1]))
    parser.add_argument("--set2-root", default=str(DEFAULT_DATASET_ROOTS[DATASET_SURFACE_SET2]))
    parser.add_argument("--surface-105q-root", default=str(DEFAULT_DATASET_ROOTS[DATASET_105Q]))
    parser.add_argument("--output-dir", default="outputs/google_static/unified_inventory")
    parser.add_argument(
        "--dem-proxy-mode",
        choices=["none", "first_per_dataset", "all"],
        default="first_per_dataset",
        help="Control DEM proxy extraction cost. Use all for a complete per-DEM proxy manifest.",
    )
    parser.add_argument("--progress-json", action="store_true")
    return parser.parse_args(argv)


def _csv(value: str) -> list[str]:
    return [part.strip() for part in str(value).split(",") if part.strip()]


def _summary(result: dict[str, object]) -> dict[str, object]:
    return {
        "num_contexts": result.get("num_contexts"),
        "num_decoder_rows": result.get("num_decoder_rows"),
        "audit_path": result.get("audit_path"),
    }


def _jsonable(value):
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


if __name__ == "__main__":
    main()
