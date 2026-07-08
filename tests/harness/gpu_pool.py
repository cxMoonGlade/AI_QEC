"""GPU pool (semaphore) in Python -- the multi-GPU interface. N slots, one per card, with
CUDA_VISIBLE_DEVICES pinning. Replaces gpu_pool.sh. USER KNOB: ECS_GPUS (pool size; default
auto-detect via nvidia-smi). 1 GPU -> jobs serialize; N GPUs -> N GPU jobs in parallel, each on
its own card; all busy -> block until one frees. The flock is held via a kept-open fd for the
acquiring process's lifetime (release() or the GpuSlot context manager drops it)."""
from __future__ import annotations

import fcntl
import os
import subprocess

_LOCK_TMPL = "/tmp/ecs_gpu.{}.lock"


def detect_gpus() -> int:
    """Pool size: ECS_GPUS if set, else count of `nvidia-smi -L` lines (fallback 1)."""
    v = os.environ.get("ECS_GPUS")
    if v:
        try:
            return max(int(v), 1)
        except ValueError:
            pass
    try:
        out = subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True,
                             timeout=15).stdout
        n = sum(1 for ln in out.splitlines() if ln.startswith("GPU "))
        return max(n, 1)
    except (FileNotFoundError, subprocess.SubprocessError):
        return 1


class GpuSlot:
    """Holds one GPU slot lock (fd kept open). Use as a context manager or call release()."""
    def __init__(self, slot: int, fd: int):
        self.slot = slot
        self._fd = fd

    def release(self) -> None:
        if self._fd is not None:
            try:
                os.close(self._fd)
            finally:
                self._fd = None

    def __enter__(self) -> "GpuSlot":
        return self

    def __exit__(self, *_a) -> None:
        self.release()


def acquire_gpu_slot() -> GpuSlot:
    """Acquire one of N slots and pin CUDA_VISIBLE_DEVICES to it. Non-blocking first pass over the
    cards; if all N are busy, BLOCK on slot 0 until it frees. Returns a GpuSlot -- keep it alive
    (or use `with acquire_gpu_slot():`) to hold the card for the duration of the GPU work."""
    n = detect_gpus()
    for i in range(n):
        fd = os.open(_LOCK_TMPL.format(i), os.O_CREAT | os.O_WRONLY, 0o644)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(fd)
            continue
        os.environ["CUDA_VISIBLE_DEVICES"] = str(i)
        os.environ["ECS_GPU_SLOT"] = str(i)
        return GpuSlot(i, fd)
    # all busy -> block until slot 0 frees
    fd = os.open(_LOCK_TMPL.format(0), os.O_CREAT | os.O_WRONLY, 0o644)
    fcntl.flock(fd, fcntl.LOCK_EX)
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    os.environ["ECS_GPU_SLOT"] = "0"
    return GpuSlot(0, fd)
