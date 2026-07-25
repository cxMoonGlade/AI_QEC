#!/usr/bin/env python3
"""Run the captured 170-call mixed-shape ``torch.linalg.pinv`` diagnostic.

This is a runtime stress/reproduction test.  It is not pytest, simulator
acceptance, scientific evidence, or a hardware-health certificate.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
from typing import Any
from uuid import uuid4


EXPECTED_CALL_COUNT = 170
EXPECTED_CALL_SCHEMA = "error_coupling_simulator.pepo_ntu_pinv_call.v1"
RESULT_SCHEMA = "error_coupling_simulator.runtime.pinv_170_diagnostic.v1"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_ROOT = (
    REPO_ROOT
    / "outputs/simulator_validation/runtime_reset_watch/isolated_runs"
    / "compressed_caps_v2_largest_capture_4b2a5f7_20260720_a1"
    / "ntu_snapshots"
)
DEFAULT_OUTPUT_PARENT = (
    REPO_ROOT
    / "outputs/simulator_validation/runtime_reset_watch/pinv_170_standalone_runs"
)


@dataclass(frozen=True, slots=True)
class CallSpec:
    call_index: int
    side: str
    side_length: int
    rtol: float
    bond: str
    sweep_index: int
    re: int


def timestamp() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="microseconds")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def append_jsonl(path: Path, value: Any) -> None:
    with path.open("ab", buffering=0) as stream:
        stream.write(canonical_bytes(value) + b"\n")
        os.fsync(stream.fileno())


def atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid4().hex}.tmp")
    try:
        with temporary.open("wb") as stream:
            stream.write(canonical_bytes(value) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        fsync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def load_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"JSON root is not an object: {path}")
    return value


def require_int(value: object, *, name: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def load_call_plan(path: Path) -> list[CallSpec]:
    payload = path.read_bytes()
    if payload and not payload.endswith(b"\n"):
        raise ValueError("call manifest has an incomplete final line")
    rows: list[dict[str, Any]] = []
    for line_number, raw in enumerate(payload.splitlines(), start=1):
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise TypeError(f"manifest row {line_number} is not an object")
        rows.append(value)
    if len(rows) != EXPECTED_CALL_COUNT:
        raise ValueError(
            f"manifest must contain exactly {EXPECTED_CALL_COUNT} calls; got {len(rows)}"
        )

    calls: list[CallSpec] = []
    for expected_index, row in enumerate(rows, start=1):
        if row.get("schema") != EXPECTED_CALL_SCHEMA:
            raise ValueError(f"call {expected_index} has an unsupported schema")
        call_index = require_int(
            row.get("pinv_call_sequence"),
            name=f"call {expected_index} sequence",
            minimum=1,
        )
        if call_index != expected_index:
            raise ValueError(f"manifest sequence is not contiguous at row {expected_index}")
        solver = row.get("solver")
        tensor = row.get("tensor")
        health = row.get("health")
        if not isinstance(solver, dict) or not isinstance(tensor, dict):
            raise TypeError(f"call {call_index} lacks solver or tensor metadata")
        if not isinstance(health, dict) or health.get("finite") is not True:
            raise ValueError(f"call {call_index} was not captured as finite")
        side = solver.get("solver_side")
        if side not in ("A", "B"):
            raise ValueError(f"call {call_index} has an invalid solver side")
        shape = tensor.get("shape")
        if (
            not isinstance(shape, list)
            or len(shape) != 2
            or type(shape[0]) is not int
            or type(shape[1]) is not int
            or shape[0] != shape[1]
            or not 1 <= shape[0] <= 1024
        ):
            raise ValueError(f"call {call_index} has an invalid square shape")
        side_length = shape[0]
        if tensor.get("dtype") != "torch.complex128":
            raise ValueError(f"call {call_index} is not complex128")
        if tensor.get("logical_nbytes") != side_length * side_length * 16:
            raise ValueError(f"call {call_index} has inconsistent logical bytes")
        rtol = solver.get("rtol")
        if (
            isinstance(rtol, bool)
            or not isinstance(rtol, (int, float))
            or not math.isfinite(rtol)
            or rtol <= 0
        ):
            raise ValueError(f"call {call_index} has an invalid rtol")
        bond = solver.get("bond")
        if not isinstance(bond, str) or not bond:
            raise ValueError(f"call {call_index} has an invalid bond")
        calls.append(
            CallSpec(
                call_index=call_index,
                side=side,
                side_length=side_length,
                rtol=float(rtol),
                bond=bond,
                sweep_index=require_int(
                    solver.get("sweep_index"),
                    name=f"call {call_index} sweep_index",
                    minimum=1,
                ),
                re=require_int(
                    solver.get("re"), name=f"call {call_index} re", minimum=1
                ),
            )
        )
    return calls


def validate_snapshot_metadata(
    *, label: str, snapshot: Path, metadata: dict[str, Any]
) -> str:
    actual_sha256 = file_sha256(snapshot)
    if metadata.get("sha256") != actual_sha256:
        raise ValueError(f"{label} snapshot SHA-256 does not match metadata")
    tensor = metadata.get("tensor")
    if not isinstance(tensor, dict):
        raise TypeError(f"{label} metadata has no tensor object")
    if tensor.get("shape") != [1024, 1024]:
        raise ValueError(f"{label} retained snapshot is not 1024 x 1024")
    if tensor.get("dtype") != "torch.complex128":
        raise ValueError(f"{label} retained snapshot is not complex128")
    solver = metadata.get("solver")
    if not isinstance(solver, dict) or solver.get("solver_side") != label:
        raise ValueError(f"{label} snapshot side metadata is inconsistent")
    return actual_sha256


def git_identity() -> dict[str, Any]:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    status = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "head": head.stdout.strip() if head.returncode == 0 else None,
        "worktree_clean": status.returncode == 0 and not status.stdout.strip(),
        "status_paths": [line[3:] for line in status.stdout.splitlines() if len(line) > 3],
    }


def nvidia_smi_identity() -> dict[str, Any]:
    command = [
        "nvidia-smi",
        "--query-gpu=name,uuid,driver_version,pstate,temperature.gpu,power.draw",
        "--format=csv,noheader,nounits",
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError) as error:
        return {"error": f"{type(error).__name__}: {error}"}
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def tensor_metadata(tensor: Any) -> dict[str, Any]:
    import torch

    value: dict[str, Any] = {
        "shape": [int(size) for size in tensor.shape],
        "stride": [int(stride) for stride in tensor.stride()],
        "dtype": str(tensor.dtype),
        "device": str(tensor.device),
        "numel": int(tensor.numel()),
        "logical_nbytes": int(tensor.numel() * tensor.element_size()),
        "contiguous": bool(tensor.is_contiguous()),
    }
    if tensor.device.type == "cuda":
        stats = torch.cuda.memory_stats(tensor.device)
        value.update(
            {
                "cuda_allocated": int(torch.cuda.memory_allocated(tensor.device)),
                "cuda_reserved": int(torch.cuda.memory_reserved(tensor.device)),
                "cuda_max_allocated": int(
                    torch.cuda.max_memory_allocated(tensor.device)
                ),
                "cuda_num_alloc_retries": int(stats.get("num_alloc_retries", 0)),
                "cuda_num_ooms": int(stats.get("num_ooms", 0)),
            }
        )
    return value


def tensor_health(tensor: Any) -> dict[str, Any]:
    import torch

    with torch.no_grad():
        finite = bool(torch.isfinite(tensor).all().item())
        has_nan = bool(torch.isnan(tensor).any().item())
        has_inf = bool(torch.isinf(tensor).any().item())
        abs_max = 0.0 if tensor.numel() == 0 else float(tensor.abs().max().item())
    return {
        "finite": finite,
        "has_nan": has_nan,
        "has_inf": has_inf,
        "abs_max": abs_max if math.isfinite(abs_max) else str(abs_max),
    }


class EventWriter:
    def __init__(self, path: Path, common: dict[str, Any]) -> None:
        self.path = path
        self.common = common
        self.sequence = 0

    def emit(self, kind: str, **fields: Any) -> None:
        self.sequence += 1
        append_jsonl(
            self.path,
            {
                **self.common,
                **fields,
                "event_sequence": self.sequence,
                "timestamp": timestamp(),
                "kind": kind,
            },
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--run-root", type=Path)
    parser.add_argument(
        "--limit",
        type=int,
        help="run a validated prefix for smoke testing; omit for all 170 calls",
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="validate inputs and runtime without executing pinv",
    )
    parser.add_argument(
        "--acknowledge-reset-risk",
        action="store_true",
        help="required for CUDA execution because this workload has reset another host",
    )
    args = parser.parse_args()
    if args.limit is not None and not 1 <= args.limit <= EXPECTED_CALL_COUNT:
        parser.error(f"--limit must be in [1, {EXPECTED_CALL_COUNT}]")
    if args.device == "cuda" and not args.preflight_only and not args.acknowledge_reset_risk:
        parser.error("CUDA execution requires --acknowledge-reset-risk")
    return args


def main() -> int:
    args = parse_args()
    input_root = args.input_root.resolve(strict=True)
    manifest = (input_root / "pinv_calls.jsonl").resolve(strict=True)
    ga_metadata_path = (input_root / "largest-GA.json").resolve(strict=True)
    gb_metadata_path = (input_root / "largest-GB.json").resolve(strict=True)
    ga_snapshot = (input_root / "largest-GA.pt").resolve(strict=True)
    gb_snapshot = (input_root / "largest-GB.pt").resolve(strict=True)

    calls = load_call_plan(manifest)
    executed_calls = calls[: args.limit] if args.limit is not None else calls
    if args.limit is None and len(executed_calls) != EXPECTED_CALL_COUNT:
        raise AssertionError("full execution plan is not exactly 170 calls")
    ga_sha256 = validate_snapshot_metadata(
        label="A", snapshot=ga_snapshot, metadata=load_json_object(ga_metadata_path)
    )
    gb_sha256 = validate_snapshot_metadata(
        label="B", snapshot=gb_snapshot, metadata=load_json_object(gb_metadata_path)
    )

    run_id = (
        f"pinv_170_{args.device}_"
        f"{datetime.now().astimezone().strftime('%Y%m%dT%H%M%S%z')}_{os.getpid()}"
    )
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.+-]{0,127}", run_id):
        raise ValueError("generated run ID is invalid")
    if args.run_root is None:
        DEFAULT_OUTPUT_PARENT.mkdir(mode=0o700, parents=True, exist_ok=True)
        run_root = DEFAULT_OUTPUT_PARENT / run_id
    else:
        run_root = args.run_root.resolve()
        run_root.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    run_root.mkdir(mode=0o700, exist_ok=False)
    fsync_directory(run_root.parent)

    boot_id_path = Path("/proc/sys/kernel/random/boot_id")
    boot_id = (
        boot_id_path.read_text(encoding="ascii").strip()
        if boot_id_path.is_file()
        else "unavailable"
    )
    source_identity = {
        "script_sha256": file_sha256(Path(__file__).resolve()),
        "manifest_sha256": file_sha256(manifest),
        "call_plan_sha256": canonical_sha256([asdict(call) for call in calls]),
        "ga_metadata_sha256": file_sha256(ga_metadata_path),
        "ga_snapshot_sha256": ga_sha256,
        "gb_metadata_sha256": file_sha256(gb_metadata_path),
        "gb_snapshot_sha256": gb_sha256,
    }
    common = {
        "schema": RESULT_SCHEMA,
        "run_id": run_id,
        "boot_id": boot_id,
        "target_device": args.device,
        "complete_call_count": EXPECTED_CALL_COUNT,
        "executed_call_count": len(executed_calls),
        "partial_prefix": len(executed_calls) != EXPECTED_CALL_COUNT,
        "source_identity": source_identity,
        "evidence_class": "runtime_diagnostic_not_release_or_scientific_evidence",
    }
    events = EventWriter(run_root / "events.jsonl", common)

    print(f"run_root={run_root}", flush=True)
    print(
        f"plan={len(executed_calls)}/{EXPECTED_CALL_COUNT} device={args.device}",
        flush=True,
    )
    print(f"plan_sha256={source_identity['call_plan_sha256']}", flush=True)

    import torch

    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable inside this process")
    target = torch.device(args.device)
    cpu_bases = {
        "A": torch.load(ga_snapshot, map_location="cpu", weights_only=True),
        "B": torch.load(gb_snapshot, map_location="cpu", weights_only=True),
    }
    for side, tensor in cpu_bases.items():
        if not isinstance(tensor, torch.Tensor):
            raise TypeError(f"side {side} snapshot is not a tensor")
        if tensor.shape != (1024, 1024) or tensor.dtype != torch.complex128:
            raise ValueError(f"side {side} snapshot tensor identity is inconsistent")
        if not tensor_health(tensor)["finite"]:
            raise ValueError(f"side {side} snapshot contains non-finite values")

    preflight = {
        **common,
        "captured_at": timestamp(),
        "host": {
            "hostname": platform.node(),
            "platform": platform.platform(),
            "python": sys.version,
            "python_executable": sys.executable,
            "nvidia_smi": nvidia_smi_identity(),
        },
        "runtime": {
            "torch": str(torch.__version__),
            "torch_cuda_build": torch.version.cuda,
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_name": (
                torch.cuda.get_device_name(target)
                if target.type == "cuda"
                else None
            ),
        },
        "repository": git_identity(),
        "input_construction": (
            "top_left_principal_submatrix_of_side_specific_largest_real_snapshot"
        ),
        "claims_exact_historical_tensor_replay": False,
        "local_fsync_only": True,
        "claims_independent_durable_observer": False,
    }
    atomic_json(run_root / "preflight.json", preflight)
    events.emit("preflight_passed", runtime=preflight["runtime"])
    print(
        f"torch={torch.__version__} cuda_build={torch.version.cuda} "
        f"cuda_available={torch.cuda.is_available()}",
        flush=True,
    )

    if args.preflight_only:
        result = {
            **common,
            "status": "preflight_passed",
            "calls_completed": 0,
            "finished_at": timestamp(),
            "claim_boundary": "no pinv call was executed",
        }
        atomic_json(run_root / "result.json", result)
        print("status=preflight_passed", flush=True)
        return 0

    base_tensors = {side: tensor.to(target) for side, tensor in cpu_bases.items()}
    side_lengths = sorted({call.side_length for call in executed_calls})
    matrix_cache = {
        (side, side_length): base[:side_length, :side_length].contiguous()
        for side, base in base_tensors.items()
        for side_length in side_lengths
    }
    if target.type == "cuda":
        torch.cuda.synchronize(target)
    events.emit(
        "inputs_staged",
        side_lengths=side_lengths,
        cached_tensors={
            f"{side}:{side_length}": tensor_metadata(tensor)
            for (side, side_length), tensor in matrix_cache.items()
        },
    )

    calls_completed = 0
    active_call: int | None = None
    started_ns = time.monotonic_ns()
    error_text: str | None = None
    result_status = "error"
    try:
        for call in executed_calls:
            active_call = call.call_index
            matrix = matrix_cache[(call.side, call.side_length)]
            call_started_ns = time.monotonic_ns()
            events.emit(
                "before_pre_pinv_sync",
                call=asdict(call),
                calls_completed=calls_completed,
                tensor=tensor_metadata(matrix),
            )
            if target.type == "cuda":
                torch.cuda.synchronize(target)
            events.emit(
                "pre_pinv_synced",
                call=asdict(call),
                calls_completed=calls_completed,
                tensor=tensor_metadata(matrix),
            )
            pinv_result = torch.linalg.pinv(matrix, rtol=call.rtol)
            events.emit(
                "pinv_returned_before_explicit_sync",
                call=asdict(call),
                calls_completed=calls_completed,
                tensor=tensor_metadata(pinv_result),
            )
            if target.type == "cuda":
                torch.cuda.synchronize(target)
            health = tensor_health(pinv_result)
            if not health["finite"]:
                raise ValueError(f"pinv result for call {call.call_index} is non-finite")
            calls_completed += 1
            elapsed = (time.monotonic_ns() - call_started_ns) / 1_000_000_000
            events.emit(
                "after_pinv_sync",
                call=asdict(call),
                calls_completed=calls_completed,
                call_elapsed_s=elapsed,
                tensor=tensor_metadata(pinv_result),
                health=health,
            )
            print(
                f"[{calls_completed:03d}/{len(executed_calls):03d}] "
                f"side={call.side} shape={call.side_length}x{call.side_length} "
                f"elapsed={elapsed:.3f}s finite=true",
                flush=True,
            )
        result_status = "passed"
    except BaseException as error:
        error_text = f"{type(error).__name__}: {error}"
        try:
            events.emit(
                "pinv_sequence_error",
                active_call=active_call,
                calls_completed=calls_completed,
                error=error_text,
            )
        except BaseException:
            pass

    sequence_elapsed = (time.monotonic_ns() - started_ns) / 1_000_000_000
    result = {
        **common,
        "status": result_status,
        "calls_completed": calls_completed,
        "active_call": active_call,
        "sequence_elapsed_s": sequence_elapsed,
        "error": error_text,
        "finished_at": timestamp(),
        "same_process_and_device_context": True,
        "all_completed_results_finite": (
            result_status == "passed" and calls_completed == len(executed_calls)
        ),
        "claim_boundary": (
            "constructed pinv runtime diagnostic only; not exact historical tensor replay, "
            "simulator acceptance, scientific evidence, or hardware-health certification"
        ),
    }
    atomic_json(run_root / "result.json", result)
    events.emit(
        "pinv_sequence_terminal",
        status=result_status,
        calls_completed=calls_completed,
        sequence_elapsed_s=sequence_elapsed,
        result_sha256=file_sha256(run_root / "result.json"),
    )
    print(
        f"status={result_status} calls_completed={calls_completed}/"
        f"{len(executed_calls)} elapsed={sequence_elapsed:.3f}s",
        flush=True,
    )
    return 0 if result_status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
