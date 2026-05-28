from __future__ import annotations

from dataclasses import dataclass
import importlib
import importlib.metadata as metadata
import json
from pathlib import Path
import time


@dataclass(frozen=True)
class BackendPolicy:
    backend: str = "cudaq"
    require_gpu: bool = True
    cudaq_target: str = "nvidia"
    cudaq_target_options: str = "fp32"


def audit_cudaq_backend(
    *,
    backend: str = "cudaq",
    require_gpu: bool = True,
    cudaq_target: str = "nvidia",
    cudaq_target_options: str = "fp32",
) -> dict[str, object]:
    """Audit CUDA-Q availability and the requested GPU target."""

    packages = {name: _package_version(name) for name in ("cudaq", "cuda-quantum")}
    warnings: list[str] = []
    errors: list[str] = []
    if str(backend) not in {"cudaq", "cudaq_nvidia", "local_observable_gpu"}:
        errors.append(f"unsupported physical backend {backend!r}; expected cudaq or local_observable_gpu")

    import_ok = False
    import_error = None
    target_name = None
    target_description = None
    gpu_count = 0
    tiny_sample = {
        "attempted": False,
        "passed": False,
        "target": str(cudaq_target),
        "target_options": str(cudaq_target_options),
        "shots": 32,
        "counts": None,
        "error": None,
    }
    started = time.perf_counter()
    try:
        cudaq = importlib.import_module("cudaq")
        import_ok = True
        try:
            gpu_count = int(cudaq.num_available_gpus())
        except Exception as exc:  # pragma: no cover - depends on CUDA-Q runtime
            warnings.append(f"failed to query CUDA-Q GPU count: {type(exc).__name__}: {exc}")
        try:
            _set_cudaq_target(cudaq, target=str(cudaq_target), options=str(cudaq_target_options))
            target = cudaq.get_target()
            target_name = str(target.name if hasattr(target, "name") else target)
            target_description = str(target)
            tiny_sample = _run_tiny_cudaq_sample(cudaq, target=str(cudaq_target), options=str(cudaq_target_options))
        except Exception as exc:  # pragma: no cover - depends on CUDA-Q runtime
            errors.append(f"failed CUDA-Q target/sample audit: {type(exc).__name__}: {exc}")
            tiny_sample["error"] = f"{type(exc).__name__}: {exc}"
    except Exception as exc:
        import_error = f"{type(exc).__name__}: {exc}"
        errors.append(f"failed to import cudaq: {import_error}")

    gpu_ready = bool(import_ok and (gpu_count > 0 or not require_gpu) and tiny_sample.get("passed"))
    if require_gpu and gpu_count <= 0:
        errors.append("CUDA-Q GPU target is required but no CUDA-Q GPU is visible")
    if require_gpu and not bool(tiny_sample.get("passed")):
        errors.append("tiny CUDA-Q GPU sample failed")
    backend_usable = bool(gpu_ready if require_gpu else import_ok and tiny_sample.get("passed"))
    status = "pass" if backend_usable and not errors else "fail"
    return {
        "schema": "scope_static_s2d_backend_audit_v2",
        "stage": "S2D_PHYS0_preflight",
        "backend_policy": {
            "backend": str(backend),
            "priority": ["cudaq"],
            "require_gpu": bool(require_gpu),
            "cudaq_target": str(cudaq_target),
            "cudaq_target_options": str(cudaq_target_options),
        },
        "packages": packages,
        "cudaq_import_ok": bool(import_ok),
        "cudaq_import_error": import_error,
        "cudaq_target": target_name,
        "cudaq_target_description": target_description,
        "cudaq_gpu_count": int(gpu_count),
        "tiny_cudaq_sample": tiny_sample,
        "backend_usable": bool(backend_usable),
        "status": status,
        "warnings": warnings,
        "errors": errors,
        "wall_clock_seconds": float(time.perf_counter() - started),
    }


def write_backend_audit(audit: dict[str, object], output_dir: str | Path) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "backend_audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    (output / "backend_audit.md").write_text(format_backend_audit_markdown(audit))


def format_backend_audit_markdown(audit: dict[str, object]) -> str:
    packages = audit.get("packages", {})
    if not isinstance(packages, dict):
        packages = {}
    lines = [
        "# S2D PHYS0 Backend Preflight",
        "",
        f"- Status: `{audit.get('status')}`",
        f"- Backend usable: `{str(bool(audit.get('backend_usable'))).lower()}`",
        f"- CUDA-Q import ok: `{str(bool(audit.get('cudaq_import_ok'))).lower()}`",
        f"- CUDA-Q target: `{audit.get('cudaq_target')}`",
        f"- CUDA-Q GPU count: `{audit.get('cudaq_gpu_count')}`",
        f"- Tiny CUDA-Q sample: `{str(bool(_tiny_sample_passed(audit))).lower()}`",
        "",
        "| package | version |",
        "| --- | --- |",
    ]
    for name in ("cudaq", "cuda-quantum"):
        lines.append(f"| {name} | `{packages.get(name)}` |")
    if audit.get("warnings"):
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {item}" for item in audit["warnings"])  # type: ignore[index]
    if audit.get("errors"):
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {item}" for item in audit["errors"])  # type: ignore[index]
    lines.append("")
    return "\n".join(lines)


def _package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _set_cudaq_target(cudaq, *, target: str, options: str) -> None:
    if options:
        cudaq.set_target(str(target), option=str(options))
    else:
        cudaq.set_target(str(target))


def _run_tiny_cudaq_sample(cudaq, *, target: str, options: str) -> dict[str, object]:
    audit: dict[str, object] = {
        "attempted": True,
        "passed": False,
        "target": str(target),
        "target_options": str(options),
        "shots": 32,
        "counts": None,
        "error": None,
    }
    try:
        kernel = cudaq.make_kernel()
        q = kernel.qalloc(1)
        kernel.h(q[0])
        kernel.mz(q[0])
        counts = cudaq.sample(kernel, shots_count=int(audit["shots"]))
        materialized = {str(key): int(value) for key, value in counts.items()}
        audit["counts"] = materialized
        audit["passed"] = sum(materialized.values()) == int(audit["shots"])
    except Exception as exc:  # pragma: no cover - depends on CUDA-Q runtime
        audit["error"] = f"{type(exc).__name__}: {exc}"
    return audit


def _tiny_sample_passed(audit: dict[str, object]) -> bool:
    tiny = audit.get("tiny_cudaq_sample")
    return isinstance(tiny, dict) and bool(tiny.get("passed"))
