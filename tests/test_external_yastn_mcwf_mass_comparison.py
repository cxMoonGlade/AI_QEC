"""Contract tests for the isolated YASTN MCWF candidate-mass comparator."""

from __future__ import annotations

import base64
import hashlib
import importlib.util
from pathlib import Path

import pytest


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


def test_yastn_direct_url_must_bind_installed_distribution_to_frozen_clone():
    adapter = _load_adapter()
    healthy = {
        "url": adapter.BASELINE_REPO.resolve().as_uri(),
        "vcs_info": {
            "vcs": "git",
            "commit_id": adapter.EXPECTED_YASTN_COMMIT,
            "requested_revision": adapter.EXPECTED_YASTN_COMMIT,
        },
    }

    assert adapter.validate_yastn_direct_url(healthy)["commit_id"] == (
        adapter.EXPECTED_YASTN_COMMIT
    )
    corrupted = {
        **healthy,
        "vcs_info": {**healthy["vcs_info"], "commit_id": "0" * 40},
    }
    with pytest.raises(RuntimeError, match="installed YASTN commit drifted"):
        adapter.validate_yastn_direct_url(corrupted)


def test_yastn_record_hash_decoder_rejects_unexpected_algorithm():
    adapter = _load_adapter()
    digest = hashlib.sha256(b"frozen payload").digest()
    encoded = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

    assert adapter.decode_record_sha256(f"sha256={encoded}") == digest.hex()
    with pytest.raises(
        RuntimeError,
        match="unsupported installed-distribution RECORD hash",
    ):
        adapter.decode_record_sha256(f"sha512={encoded}")


def test_yastn_source_tree_verification_is_bidirectional_and_fail_closed():
    adapter = _load_adapter()
    clone = {
        "yastn/__init__.py": "a" * 64,
        "yastn/tn/mps/_mps_obc.py": "b" * 64,
    }
    installed = {
        **clone,
        "yastn/_version.py": "c" * 64,
    }

    healthy = adapter.validate_yastn_source_tree_hashes(
        installed_sha256=installed,
        clone_sha256=clone,
    )
    assert healthy["all_comparable_files_match"] is True
    assert healthy["comparable_python_file_count"] == 2
    assert healthy["generated_python_files"] == ["yastn/_version.py"]

    with pytest.raises(RuntimeError, match="source-tree hash mismatch"):
        adapter.validate_yastn_source_tree_hashes(
            installed_sha256={**installed, "yastn/__init__.py": "d" * 64},
            clone_sha256=clone,
        )
    with pytest.raises(RuntimeError, match="source-tree path mismatch"):
        adapter.validate_yastn_source_tree_hashes(
            installed_sha256={**installed, "yastn/unexpected.py": "e" * 64},
            clone_sha256=clone,
        )
