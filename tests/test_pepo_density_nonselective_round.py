"""Process-isolated nonselective PEPO comparison against an exact reference."""

from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import secrets
import subprocess
import sys

from conftest import requires_cuda


WORKER = Path(__file__).parent / "_support" / "pepo_nonselective_worker.py"
EXPECTED_MAX_ABS_LIMIT = 1.0e-2
NATIVE_FATAL_CODES = {
    128 + signal.SIGABRT,
    128 + signal.SIGSEGV,
    -signal.SIGABRT,
    -signal.SIGSEGV,
}


class NativeWorkerFailure(RuntimeError):
    def __init__(self, returncode: int, output: str):
        super().__init__(output)
        self.returncode = int(returncode)
        self.output = output


def _run_fresh_worker(arguments: list[str], log_path: Path) -> None:
    with log_path.open("wb") as log:
        # Deliberately inherit the already-registered acceptance process group.
        # The outer service timeout/signal cleanup therefore owns the coordinator
        # and either worker atomically; starting a nested session would detach it.
        completed = subprocess.run(
            [sys.executable, str(WORKER), *arguments],
            cwd=Path(__file__).resolve().parents[1],
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if completed.returncode in NATIVE_FATAL_CODES:
        raise NativeWorkerFailure(
            completed.returncode,
            log_path.read_text(encoding="utf-8", errors="replace"),
        )
    if completed.returncode != 0:
        raise AssertionError(log_path.read_text(encoding="utf-8", errors="replace"))


@requires_cuda
def test_truncating_nonselective_round_matches_exact_reference(tmp_path: Path) -> None:
    """Compare unchanged maps and thresholds across independent CUDA lifetimes."""

    artifact = tmp_path / "reference.npy"
    manifest = tmp_path / "reference.json"
    result_path = tmp_path / "result.json"
    nonce = secrets.token_hex(16)

    native_failure: NativeWorkerFailure | None = None
    try:
        _run_fresh_worker(
            ["reference", nonce, str(artifact), str(manifest)],
            tmp_path / "reference.log",
        )
        _run_fresh_worker(
            ["carrier", nonce, str(artifact), str(manifest), str(result_path)],
            tmp_path / "carrier.log",
        )

        reference_evidence = json.loads(manifest.read_text(encoding="utf-8"))
        result = json.loads(result_path.read_text(encoding="utf-8"))
        assert result["schema"] == "error_coupling_simulator.pepo_nonselective_result.v1"
        assert result["nonce"] == nonce
        assert result["cap_was_binding"] is True
        assert int(result["ntu_entries"]) > 0
        assert float(result["max_abs_limit"]) == EXPECTED_MAX_ABS_LIMIT
        assert float(result["max_abs_difference"]) <= EXPECTED_MAX_ABS_LIMIT
        print(
            "PEPO_NONSELECTIVE_EVIDENCE="
            + json.dumps(
                {"reference": reference_evidence, "result": result},
                sort_keys=True,
                allow_nan=False,
            )
        )
    except NativeWorkerFailure as exc:
        native_failure = exc
    finally:
        # The 5.77-GiB reference is deliberately ephemeral.  Small provenance
        # evidence is copied into the durable service log before this unlink.
        for ephemeral in (
            artifact,
            artifact.with_name(f".{artifact.name}.tmp"),
            manifest.with_name(f".{manifest.name}.tmp"),
            result_path.with_name(f".{result_path.name}.tmp"),
        ):
            ephemeral.unlink(missing_ok=True)

    if native_failure is not None:
        sys.stderr.write(native_failure.output)
        sys.stderr.flush()
        normalized = (
            native_failure.returncode
            if native_failure.returncode > 0
            else 128 + abs(native_failure.returncode)
        )
        os._exit(normalized)
