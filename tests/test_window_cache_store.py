from pathlib import Path

import torch

from scope_static.fault_graph import FaultGraph
from scope_static.likelihood import build_window_batch_nll_cache, build_window_nll_caches
from scope_static.window_cache_store import (
    load_window_batch_cache,
    save_window_batch_cache,
    window_batch_cache_file,
    window_batch_cache_key,
)
from scope_static.windows import ObservationWindow


def _tiny_graph():
    return FaultGraph.from_raw_masks(
        torch.tensor(
            [
                [1, 0, 1],
                [0, 1, 1],
            ],
            dtype=torch.bool,
        ),
        num_detectors=2,
        num_observables=0,
        residual_rank=1,
        canonicalize_duplicate_masks=False,
    )


def test_window_batch_cache_key_changes_with_identity():
    graph = _tiny_graph()
    windows = [ObservationWindow(name="left", bits=(0,), kind="test")]

    first = window_batch_cache_key(graph, windows, {"sample_id": "sample_00", "slice": [0, 10]})
    same = window_batch_cache_key(graph, windows, {"slice": [0, 10], "sample_id": "sample_00"})
    different = window_batch_cache_key(graph, windows, {"sample_id": "sample_01", "slice": [0, 10]})

    assert first == same
    assert first != different


def test_window_batch_cache_round_trips_with_key(tmp_path: Path):
    graph = _tiny_graph()
    windows = [
        ObservationWindow(name="left", bits=(0,), kind="test"),
        ObservationWindow(name="full", bits=(0, 1), kind="test"),
    ]
    observations = torch.tensor([[0, 0], [1, 0], [1, 1], [1, 1]], dtype=torch.bool)
    batch = build_window_batch_nll_cache(
        build_window_nll_caches(graph, observations, windows, aggregate_unique=True),
    )
    key = window_batch_cache_key(graph, windows, {"sample_id": "sample_00", "role": "heldout"})
    path = window_batch_cache_file(tmp_path, key)

    save_window_batch_cache(path, key=key, cache=batch, metadata={"role": "heldout"})
    loaded = load_window_batch_cache(path, expected_key=key, device="cpu")
    assert loaded.status == "hit"
    assert loaded.cache is not None
    assert torch.equal(loaded.cache.flat_states, batch.flat_states)
    assert torch.equal(loaded.cache.flat_counts, batch.flat_counts)
    assert torch.equal(loaded.cache.state_offsets, batch.state_offsets)
    assert torch.equal(loaded.cache.window_total_counts, batch.window_total_counts)
    assert loaded.metadata["role"] == "heldout"

    mismatch = load_window_batch_cache(path, expected_key="not-the-key", device="cpu")
    assert mismatch.status == "key_mismatch"
    assert mismatch.cache is None
