from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "gcapeps_finite_memory_logical_memory.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("_test_fm_memory", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_array_roots_deduplicate_within_category_and_reject_cross_alias():
    module = _load()
    root = np.zeros(16, dtype=np.complex128)
    view = root.reshape(4, 4)[:, :2]
    gauge = np.ones(3, dtype=np.float64)
    sample = module.measure_logical_memory(
        label="deduplicate",
        tensor_role="gc_residual",
        carrier_arrays=(root, view),
        gauge_arrays=(gauge,),
        frame_payloads=({"frame": 1},),
        ledger_payloads=({"ledger": 2},),
    )
    assert sample.carrier_tensor_bytes == root.nbytes
    assert sample.gauge_spectrum_bytes == gauge.nbytes
    with pytest.raises(ValueError, match="aliases categories"):
        module.measure_logical_memory(
            label="bad-alias",
            tensor_role="gc_residual",
            carrier_arrays=(root,),
            evidence_auxiliary_arrays=(view,),
        )


def test_plain_rejects_frame_and_canonical_json_rejects_nonfinite():
    module = _load()
    with pytest.raises(ValueError, match="frame_bytes=0"):
        module.measure_logical_memory(
            label="plain-frame",
            tensor_role="plain_physical",
            frame_payloads=({"not": "plain"},),
        )
    with pytest.raises(ValueError):
        module.measure_logical_memory(
            label="nan-ledger",
            tensor_role="gc_residual",
            ledger_payloads=({"value": float("nan")},),
        )


def test_tracker_separates_committed_algorithm_and_evidence_peaks():
    module = _load()
    committed = module.measure_logical_memory(
        label="committed",
        tensor_role="gc_residual",
        carrier_arrays=(np.zeros(8, dtype=np.complex128),),
        frame_payloads=({"revision": 0},),
        ledger_payloads=([],),
    )
    coexistence = module.measure_logical_memory(
        label="old-plus-candidate",
        tensor_role="gc_residual",
        carrier_arrays=(
            np.zeros(8, dtype=np.complex128),
            np.zeros(16, dtype=np.complex128),
        ),
        frame_payloads=({"revision": 0}, {"revision": 1}),
        ledger_payloads=([], [{"operation": 0}]),
    )
    evidence = module.measure_logical_memory(
        label="instrumented-shadow",
        tensor_role="none",
        evidence_auxiliary_arrays=(
            np.zeros(32, dtype=np.complex128),
        ),
        evidence_auxiliary_ledger_payloads=(
            {"shadow": True},
        ),
    )
    tracker = module.LogicalMemoryTracker(
        tensor_role="gc_residual",
        evidence=True,
    )
    tracker.sample_committed(committed)
    tracker.sample_algorithm(coexistence)
    tracker.sample_committed(committed, final=True)
    tracker.sample_evidence(evidence)
    report = tracker.report()
    assert report["final_committed_owned_logical_bytes"] == (
        committed.total_owned_logical_bytes
    )
    assert report["max_committed_owned_logical_bytes"] == (
        committed.total_owned_logical_bytes
    )
    assert report["max_sampled_algorithm_owned_logical_bytes"] == (
        coexistence.total_owned_logical_bytes
    )
    assert report["max_sampled_evidence_owned_logical_bytes"] == (
        evidence.evidence_owned_logical_bytes
    )


def test_performance_report_omits_evidence_fields():
    module = _load()
    sample = module.measure_logical_memory(
        label="final",
        tensor_role="plain_physical",
        carrier_arrays=(np.zeros(2, dtype=np.complex128),),
        ledger_payloads=([],),
    )
    tracker = module.LogicalMemoryTracker(
        tensor_role="plain_physical",
        evidence=False,
    )
    tracker.sample_committed(sample, final=True)
    report = tracker.report()
    assert "max_sampled_evidence_owned_logical_bytes" not in report
    assert "max_sampled_evidence_sample" not in report
