"""GPU pool (semaphore) in Python -- the multi-GPU interface.

N slots, one per card. Replaces gpu_pool.sh. USER KNOB: ECS_GPUS (pool size; default
auto-detect via nvidia-smi). 1 GPU -> jobs serialize; N GPUs -> N GPU jobs in parallel, each on
its own card; all busy -> block until one frees. The flock is held via a kept-open fd for the
acquiring process's lifetime (release() or the GpuSlot context manager drops it).

Acquiring a slot never mutates the harness process's environment. Call ``GpuSlot.child_env()``
to make a private child-process environment with ``CUDA_VISIBLE_DEVICES`` and ``ECS_GPU_SLOT``
pinned to the leased card. This keeps concurrent launcher threads from racing through shared
``os.environ`` state.
"""
from __future__ import annotations

import fcntl
import os
import subprocess
from collections.abc import Mapping

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

    def child_env(self, base_env: Mapping[str, str] | None = None) -> dict[str, str]:
        """Return a private environment pinned to this slot.

        ``base_env`` is copied, never mutated. When it is omitted, the current parent
        environment is copied. The caller must pass the returned mapping explicitly to its
        subprocess launcher.
        """
        env = dict(os.environ if base_env is None else base_env)
        env["CUDA_VISIBLE_DEVICES"] = str(self.slot)
        env["ECS_GPU_SLOT"] = str(self.slot)
        return env


def acquire_gpu_slot() -> GpuSlot:
    """Acquire one of N slots without mutating the parent environment.

    The first pass over the cards is non-blocking; if all N are busy, block on slot 0 until it
    frees. Keep the returned ``GpuSlot`` alive (or use it as a context manager) for the duration
    of the GPU work, and pass ``slot.child_env(...)`` to the child process.
    """
    n = detect_gpus()
    for i in range(n):
        fd = os.open(_LOCK_TMPL.format(i), os.O_CREAT | os.O_WRONLY, 0o644)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(fd)
            continue
        return GpuSlot(i, fd)
    # all busy -> block until slot 0 frees
    fd = os.open(_LOCK_TMPL.format(0), os.O_CREAT | os.O_WRONLY, 0o644)
    fcntl.flock(fd, fcntl.LOCK_EX)
    return GpuSlot(0, fd)
