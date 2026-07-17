"""Contract tests for the isolated YASTN MCWF candidate-mass comparator."""

from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "external_baselines" / "run_yastn_mcwf_mass_comparison.py"


def _load_adapter():
    spec = importlib.util.spec_from_file_location("yastn_mcwf_mass_adapter", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_yastn_mcwf_mass_analysis_rejects_corrupted_candidate_mass():
    adapter = _load_adapter()
    healthy = adapter.analyze_candidate_masses(
        initial_norm_squared=1.0,
        no_jump_norm_squared=1.0 / 4096.0,
        jump_norms_squared=[1.0] * 6,
    )
    corrupted = adapter.analyze_candidate_masses(
        initial_norm_squared=1.0,
        no_jump_norm_squared=1.0 / 4096.0,
        jump_norms_squared=[1.0] * 5 + [0.0],
    )

    assert healthy["candidate_mass"] == 6.0 + 1.0 / 4096.0
    assert healthy["candidate_mass_residual"] == 5.0 + 1.0 / 4096.0
    assert healthy["matches_frozen_reference"] is True
    assert corrupted["matches_frozen_reference"] is False
    assert corrupted["corruption_falsifier_detected"] is True
