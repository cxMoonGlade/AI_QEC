from __future__ import annotations

import argparse
import json
from pathlib import Path

from scope_static.experiments.s2d_config import load_s2d_physical_config
from scope_static.physical.preflight import audit_aer_backend, write_backend_audit
from scope_static.physical.teacher import generate_physical_teacher_dataset


def run_s2d_gpu_smoke(
    config_path: str | Path | None = None,
    *,
    output_dir: str | Path = "outputs/scope_static/S2D_GPU_smoke",
    teacher_smoke: bool = False,
    profile: str | None = None,
    shots: int | None = None,
) -> dict[str, object]:
    cfg = load_s2d_physical_config(config_path)
    if profile is not None:
        cfg["profile"] = str(profile)
    if shots is not None:
        cfg["shots"] = int(shots)
    cfg.setdefault("backend", "qiskit_aer_gpu")
    cfg.setdefault("require_gpu", True)
    cfg.setdefault("allow_cpu_aer_fallback", False)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    torch_audit = _torch_cuda_audit()
    aer_audit = audit_aer_backend(
        backend=str(cfg.get("backend", "qiskit_aer_gpu")),
        require_gpu=bool(cfg.get("require_gpu", True)),
        allow_cpu_aer_fallback=bool(cfg.get("allow_cpu_aer_fallback", False)),
    )
    preflight_dir = output / "S2D_PHYS0_preflight"
    write_backend_audit(aer_audit, preflight_dir)
    teacher = None
    if bool(teacher_smoke):
        teacher = generate_physical_teacher_dataset(
            cfg,
            output_dir=output / "S2D_PHYS1_teacher",
            preflight_dir=preflight_dir,
        )
    result = {
        "schema": "scope_static_s2d_gpu_smoke_v1",
        "output_dir": str(output),
        "torch_cuda": torch_audit,
        "aer_backend": {
            "status": aer_audit.get("status"),
            "backend_usable": aer_audit.get("backend_usable"),
            "simulator_device": aer_audit.get("simulator_device"),
            "tiny_density_matrix_gpu_simulation": aer_audit.get("tiny_density_matrix_gpu_simulation"),
            "errors": aer_audit.get("errors", []),
        },
        "teacher_smoke": teacher,
        "command_note": "Use this module for streamed GPU checks; avoid `conda run --no-capture-output ... python -c ...` in sandboxed agent sessions.",
    }
    (output / "gpu_smoke.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def _torch_cuda_audit() -> dict[str, object]:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - torch is expected in aiqec
        return {"import_ok": False, "error": f"{type(exc).__name__}: {exc}"}
    available = bool(torch.cuda.is_available())
    return {
        "import_ok": True,
        "torch_version": str(torch.__version__),
        "torch_cuda_version": str(torch.version.cuda),
        "cuda_available": available,
        "device_count": int(torch.cuda.device_count()) if available else 0,
        "device_name": torch.cuda.get_device_name(0) if available else None,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run a GPU visibility smoke for torch and Qiskit Aer.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/scope_static/S2D_GPU_smoke"))
    parser.add_argument("--teacher-smoke", action="store_true")
    parser.add_argument("--profile", type=str, default=None)
    parser.add_argument("--shots", type=int, default=None)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    result = run_s2d_gpu_smoke(
        args.config,
        output_dir=args.output_dir,
        teacher_smoke=args.teacher_smoke,
        profile=args.profile,
        shots=args.shots,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.strict:
        torch_ok = bool(result["torch_cuda"].get("cuda_available"))  # type: ignore[index,union-attr]
        aer_ok = bool(result["aer_backend"].get("backend_usable"))  # type: ignore[index,union-attr]
        if not torch_ok or not aer_ok:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
