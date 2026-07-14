from __future__ import annotations

from pathlib import Path

from harness import gpu_pool


def _isolated_pool(monkeypatch, tmp_path: Path, *, slots: int) -> None:
    monkeypatch.setattr(gpu_pool, "_LOCK_TMPL", str(tmp_path / "ecs_gpu.{}.lock"))
    monkeypatch.setattr(gpu_pool, "detect_gpus", lambda: slots)


def test_acquire_does_not_mutate_parent_and_child_env_is_pure(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _isolated_pool(monkeypatch, tmp_path, slots=1)
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "parent-visible")
    monkeypatch.setenv("ECS_GPU_SLOT", "parent-slot")
    parent_before = dict(gpu_pool.os.environ)
    base = {"KEEP": "yes", "CUDA_VISIBLE_DEVICES": "base-visible"}

    with gpu_pool.acquire_gpu_slot() as slot:
        assert slot.slot == 0
        assert dict(gpu_pool.os.environ) == parent_before

        child = slot.child_env(base)
        assert child == {
            "KEEP": "yes",
            "CUDA_VISIBLE_DEVICES": "0",
            "ECS_GPU_SLOT": "0",
        }
        assert base == {"KEEP": "yes", "CUDA_VISIBLE_DEVICES": "base-visible"}
        assert dict(gpu_pool.os.environ) == parent_before


def test_child_env_without_base_copies_parent(monkeypatch, tmp_path: Path) -> None:
    _isolated_pool(monkeypatch, tmp_path, slots=1)
    monkeypatch.setenv("UNCHANGED", "parent-value")
    parent_before = dict(gpu_pool.os.environ)

    with gpu_pool.acquire_gpu_slot() as slot:
        child = slot.child_env()

    assert child["UNCHANGED"] == "parent-value"
    assert child["CUDA_VISIBLE_DEVICES"] == "0"
    assert child["ECS_GPU_SLOT"] == "0"
    assert child is not gpu_pool.os.environ
    assert dict(gpu_pool.os.environ) == parent_before


def test_flock_assigns_distinct_slots_and_release_makes_slot_reusable(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _isolated_pool(monkeypatch, tmp_path, slots=2)

    first = gpu_pool.acquire_gpu_slot()
    second = gpu_pool.acquire_gpu_slot()
    try:
        assert (first.slot, second.slot) == (0, 1)
        assert first.child_env({})["CUDA_VISIBLE_DEVICES"] == "0"
        assert second.child_env({})["CUDA_VISIBLE_DEVICES"] == "1"
        first.release()

        with gpu_pool.acquire_gpu_slot() as reused:
            assert reused.slot == 0
    finally:
        first.release()
        second.release()
