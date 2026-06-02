from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import threading
import time
from typing import Any

import yaml

from scope_static.mechanism_discovery.google_unit_source import (
    DEFAULT_OUTPUT_DIR,
    run_stage4_google_unit_source_expansion,
)


DEFAULT_CONFIG = Path("configs/scope_static/stage4_google_unit_source_expansion_v1.yaml")
SAFE_SMOKE_BOOTSTRAP_REPLICATES = 16
SAFE_SMOKE_REPEAT_SEED_COUNT = 1
SAFE_SMOKE_K = 8


def run_stage4_google_unit_source_expansion_from_config(
    *,
    config_path: str | Path | None = None,
    teacher_dir: str | Path | None = None,
    google_stage3a_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    allow_heavy_run: bool = False,
) -> dict[str, object]:
    cfg = _load_config(config_path)
    teacher = Path(teacher_dir if teacher_dir is not None else str(cfg.get("teacher_dir", "")))
    google = Path(google_stage3a_dir if google_stage3a_dir is not None else str(cfg.get("google_stage3a_dir", "")))
    if not str(teacher) or not str(google):
        raise ValueError("stage4 Google-unit source expansion requires teacher_dir and google_stage3a_dir")
    bootstrap_replicates = int(cfg.get("bootstrap_replicates", 256))
    repeat_seed_count = int(cfg.get("repeat_seed_count", 3))
    k = int(cfg.get("k", 32))
    _assert_run_allowed(
        cfg,
        allow_heavy_run=bool(allow_heavy_run),
        bootstrap_replicates=bootstrap_replicates,
        repeat_seed_count=repeat_seed_count,
        k=k,
    )
    resolved_output = output_dir if output_dir is not None else cfg.get("output_dir", DEFAULT_OUTPUT_DIR)
    memory_guard_gib = cfg.get("memory_guard_gib")

    def _run() -> dict[str, object]:
        return run_stage4_google_unit_source_expansion(
            teacher_dir=teacher,
            google_stage3a_dir=google,
            output_dir=resolved_output,
            assignment_geometry_dir=cfg.get("assignment_geometry_dir"),
            source_pretrain_dir=cfg.get("source_pretrain_dir"),
            seed=int(cfg.get("seed", 0)),
            k=k,
            shotblock_size=int(cfg.get("shotblock_size", 16)),
            max_source_shots_per_record=cfg.get("max_source_shots_per_record"),
            mixture_component_count=int(cfg.get("mixture_component_count", 3)),
            design_fraction=float(cfg.get("design_fraction", 0.50)),
            validation_fraction=float(cfg.get("validation_fraction", 0.25)),
            min_missing_mode_mass=float(cfg.get("min_missing_mode_mass", 0.02)),
            bootstrap_replicates=bootstrap_replicates,
            repeat_seed_count=repeat_seed_count,
        )

    result = _run_with_memory_guard(
        _run,
        output_dir=Path(resolved_output),
        limit_gib=None if memory_guard_gib in (None, "") else float(memory_guard_gib),
        interval_seconds=float(cfg.get("memory_guard_interval_seconds", 1.0)),
    )
    print("S4.6 Google-unit source expansion complete")
    print(f"decision={result.get('decision')}")
    print(f"output={result.get('output_dir')}")
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run S4.6 Google-unit controlled source expansion.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--teacher-dir", type=Path)
    parser.add_argument("--google-stage3a-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--allow-heavy-run",
        action="store_true",
        help="Actually run the full S4.6 closeout. Without this flag, only explicit smoke configs are allowed.",
    )
    args = parser.parse_args(argv)
    run_stage4_google_unit_source_expansion_from_config(
        config_path=args.config,
        teacher_dir=args.teacher_dir,
        google_stage3a_dir=args.google_stage3a_dir,
        output_dir=args.output_dir,
        allow_heavy_run=args.allow_heavy_run,
    )


def _load_config(path: str | Path | None) -> dict[str, Any]:
    if path is None or not Path(path).exists():
        return {}
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Stage 4 Google-unit source expansion config must be a mapping")
    section = data.get("stage4_google_unit_source_expansion_v1", data)
    if not isinstance(section, dict):
        raise ValueError("stage4_google_unit_source_expansion_v1 config section must be a mapping")
    return dict(section)


def _assert_run_allowed(
    cfg: dict[str, Any],
    *,
    allow_heavy_run: bool,
    bootstrap_replicates: int,
    repeat_seed_count: int,
    k: int,
) -> None:
    if allow_heavy_run or bool(cfg.get("allow_heavy_run", False)):
        return
    execution_mode = str(cfg.get("execution_mode", "closeout")).lower()
    smoke_budget = (
        execution_mode == "smoke"
        and int(bootstrap_replicates) <= SAFE_SMOKE_BOOTSTRAP_REPLICATES
        and int(repeat_seed_count) <= SAFE_SMOKE_REPEAT_SEED_COUNT
        and int(k) <= SAFE_SMOKE_K
    )
    if smoke_budget:
        return
    raise RuntimeError(
        "Refusing to run S4.6 Google-unit source expansion without explicit heavy-run approval. "
        "This closeout can rebuild source modes and run paired bootstrap/seed-split repeats on real Google-unit artifacts. "
        "Use --allow-heavy-run only when you intentionally want the full run, or set execution_mode: smoke with "
        f"bootstrap_replicates <= {SAFE_SMOKE_BOOTSTRAP_REPLICATES}, "
        f"repeat_seed_count <= {SAFE_SMOKE_REPEAT_SEED_COUNT}, and k <= {SAFE_SMOKE_K}."
    )


def _run_with_memory_guard(
    run: Any,
    *,
    output_dir: Path,
    limit_gib: float | None,
    interval_seconds: float,
) -> dict[str, object]:
    if limit_gib is None or float(limit_gib) <= 0.0:
        return run()
    limit_bytes = int(float(limit_gib) * (1024**3))
    stop = threading.Event()
    output_dir.mkdir(parents=True, exist_ok=True)

    def monitor() -> None:
        peak = 0
        while not stop.wait(max(0.1, float(interval_seconds))):
            rss = _current_rss_bytes()
            peak = max(peak, rss)
            if rss > limit_bytes:
                trip = {
                    "schema": "scope_static_stage4_6_memory_guard_trip_v1",
                    "reason": "rss_exceeded_memory_guard_gib",
                    "memory_guard_gib": float(limit_gib),
                    "rss_gib": rss / float(1024**3),
                    "peak_rss_gib": peak / float(1024**3),
                    "pid": int(os.getpid()),
                }
                (output_dir / "memory_guard_trip.json").write_text(json.dumps(trip, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                os._exit(75)

    thread = threading.Thread(target=monitor, name="s4_6_memory_guard", daemon=True)
    thread.start()
    try:
        return run()
    finally:
        stop.set()
        thread.join(timeout=2.0)


def _current_rss_bytes() -> int:
    try:
        for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
    except OSError:
        return 0
    return 0


if __name__ == "__main__":
    main()
