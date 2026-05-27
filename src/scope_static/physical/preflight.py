from __future__ import annotations

from dataclasses import dataclass
import importlib
import importlib.metadata as metadata
import json
from pathlib import Path
import time
import warnings


@dataclass(frozen=True)
class BackendPolicy:
    backend: str = "qiskit_aer_gpu"
    require_gpu: bool = True
    allow_cpu_aer_fallback: bool = False


def audit_aer_backend(
    *,
    backend: str = "qiskit_aer_gpu",
    require_gpu: bool = True,
    allow_cpu_aer_fallback: bool = False,
) -> dict[str, object]:
    """Audit the shared qiskit_aer namespace and enforce GPU-first priority."""

    packages = {name: _package_version(name) for name in ("qiskit", "qiskit-aer", "qiskit-aer-gpu")}
    warnings: list[str] = []
    errors: list[str] = []
    if packages["qiskit-aer"] is not None and packages["qiskit-aer-gpu"] is not None:
        warnings.append("both qiskit-aer and qiskit-aer-gpu are installed and share the qiskit_aer namespace")
    if backend == "qiskit_aer_gpu" and packages["qiskit-aer-gpu"] is None:
        errors.append("backend requires qiskit-aer-gpu, but the package is not installed")

    import_ok = False
    namespace_version = None
    namespace_file = None
    simulator_constructed = False
    simulator_device = None
    tiny_simulation = {
        "attempted": False,
        "passed": False,
        "method": "density_matrix",
        "device": "GPU" if backend == "qiskit_aer_gpu" or require_gpu else "CPU",
        "shots": 32,
        "counts": None,
        "error": None,
    }
    import_error = None
    simulator_error = None

    try:
        qiskit_aer = importlib.import_module("qiskit_aer")
        import_ok = True
        namespace_version = getattr(qiskit_aer, "__version__", None)
        namespace_file = getattr(qiskit_aer, "__file__", None)
        try:
            from qiskit_aer import AerSimulator  # type: ignore

            kwargs = {"method": "density_matrix"}
            if backend == "qiskit_aer_gpu" or require_gpu:
                kwargs["device"] = "GPU"
            simulator = AerSimulator(**kwargs)
            simulator_constructed = True
            simulator_device = str(getattr(getattr(simulator, "options", None), "device", kwargs.get("device", "CPU")))
            if simulator_device == "GPU" or require_gpu:
                tiny_simulation = _run_tiny_density_matrix_simulation(AerSimulator)
                for record in tiny_simulation.get("warnings", []):  # type: ignore[union-attr]
                    if isinstance(record, dict):
                        warnings.append(f"{record.get('category')}: {record.get('message')}")
        except Exception as exc:  # pragma: no cover - exercised only with local Aer installs
            simulator_error = f"{type(exc).__name__}: {exc}"
            errors.append(f"failed to construct AerSimulator: {simulator_error}")
    except Exception as exc:
        import_error = f"{type(exc).__name__}: {exc}"
        errors.append(f"failed to import qiskit_aer: {import_error}")

    if namespace_version and packages["qiskit-aer-gpu"] and namespace_version != packages["qiskit-aer-gpu"]:
        message = "qiskit_aer namespace version does not match qiskit-aer-gpu metadata; CPU Aer may have overwritten GPU files"
        if require_gpu or backend == "qiskit_aer_gpu":
            errors.append(message)
        else:
            warnings.append(message)
    gpu_device_selected = simulator_device == "GPU"
    tiny_gpu_passed = bool(tiny_simulation.get("passed")) if gpu_device_selected else not require_gpu
    gpu_ready = bool(
        import_ok
        and simulator_constructed
        and packages["qiskit-aer-gpu"] is not None
        and gpu_device_selected
        and tiny_gpu_passed
    )
    cpu_fallback_ready = bool(import_ok and simulator_constructed and packages["qiskit-aer"] is not None)
    if require_gpu and not gpu_ready:
        errors.append("GPU Aer is required for default S2D runs but is not ready")
    if require_gpu and gpu_device_selected and not tiny_gpu_passed:
        errors.append("tiny density_matrix GPU simulation failed")
    if not require_gpu and not gpu_ready and cpu_fallback_ready and not allow_cpu_aer_fallback:
        errors.append("CPU Aer fallback is available but allow_cpu_aer_fallback is false")

    backend_usable = gpu_ready if require_gpu else bool(gpu_ready or (allow_cpu_aer_fallback and cpu_fallback_ready))
    status = "pass" if backend_usable and not errors else "fail"
    return {
        "schema": "scope_static_s2d_backend_audit_v1",
        "stage": "S2D_PHYS0_preflight",
        "backend_policy": {
            "backend": backend,
            "priority": ["qiskit-aer-gpu", "qiskit-aer"],
            "require_gpu": bool(require_gpu),
            "allow_cpu_aer_fallback": bool(allow_cpu_aer_fallback),
        },
        "packages": packages,
        "qiskit_aer_import_ok": bool(import_ok),
        "qiskit_aer_import_error": import_error,
        "qiskit_aer_namespace_version": namespace_version,
        "qiskit_aer_namespace_file": namespace_file,
        "gpu_simulator_constructed": bool(simulator_constructed and gpu_device_selected),
        "simulator_device": simulator_device,
        "simulator_error": simulator_error,
        "tiny_density_matrix_gpu_simulation": tiny_simulation,
        "backend_usable": bool(backend_usable),
        "status": status,
        "warnings": warnings,
        "errors": errors,
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
        f"- Import ok: `{str(bool(audit.get('qiskit_aer_import_ok'))).lower()}`",
        f"- Simulator device: `{audit.get('simulator_device')}`",
        f"- Tiny density-matrix GPU simulation: `{str(bool(_tiny_sim_passed(audit))).lower()}`",
        "",
        "| package | version |",
        "| --- | --- |",
    ]
    for name in ("qiskit", "qiskit-aer-gpu", "qiskit-aer"):
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


def _run_tiny_density_matrix_simulation(AerSimulator) -> dict[str, object]:
    audit: dict[str, object] = {
        "attempted": True,
        "passed": False,
        "method": "density_matrix",
        "device": "GPU",
        "shots": 32,
        "counts": None,
        "error": None,
        "warnings": [],
    }
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(1, 1)
    qc.h(0)
    qc.measure(0, 0)
    errors = []
    warning_records: list[dict[str, str]] = []
    for attempt in range(3):
        try:
            simulator = AerSimulator(method="density_matrix", device="GPU")
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                result = simulator.run(qc, shots=int(audit["shots"]), seed_simulator=17 + attempt).result()
            counts = {str(key): int(value) for key, value in result.get_counts().items()}
            audit["counts"] = counts
            audit["passed"] = sum(counts.values()) == int(audit["shots"])
            warning_records.extend(_warning_records(caught))
            audit["warnings"] = _dedupe_warning_records(warning_records)
            audit["attempts"] = attempt + 1
            audit["retry_errors"] = errors
            if bool(audit["passed"]):
                audit["error"] = None
                return audit
        except Exception as exc:  # pragma: no cover - depends on optional GPU runtime
            errors.append(f"{type(exc).__name__}: {exc}")
            time.sleep(0.25)
    audit["attempts"] = 3
    audit["retry_errors"] = errors
    audit["error"] = errors[-1] if errors else "tiny simulation did not return counts"
    return audit


def _tiny_sim_passed(audit: dict[str, object]) -> bool:
    tiny = audit.get("tiny_density_matrix_gpu_simulation")
    return isinstance(tiny, dict) and bool(tiny.get("passed"))


def _warning_records(caught: list[warnings.WarningMessage]) -> list[dict[str, str]]:
    records = []
    seen = set()
    for item in caught:
        record = {"category": item.category.__name__, "message": str(item.message)}
        key = (record["category"], record["message"])
        if key in seen:
            continue
        seen.add(key)
        records.append(record)
    return records


def _dedupe_warning_records(records: list[dict[str, str]]) -> list[dict[str, str]]:
    out = []
    seen = set()
    for record in records:
        key = (record.get("category", ""), record.get("message", ""))
        if key in seen:
            continue
        seen.add(key)
        out.append({"category": key[0], "message": key[1]})
    return out
