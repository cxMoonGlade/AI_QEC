from __future__ import annotations

import importlib
from pathlib import Path

from scope_static.mechanism_discovery.baseline_registry import (
    BASELINE_REGISTRY,
    DOC_BASELINE_KEYS,
    PROTOCOL_BASELINE_KEYS,
    baseline_registry_audit,
    write_baseline_registry_audit,
)


def test_registry_covers_all_baselines_named_in_docs_baselines() -> None:
    assert set(DOC_BASELINE_KEYS) <= set(BASELINE_REGISTRY)
    for key in DOC_BASELINE_KEYS:
        entry = BASELINE_REGISTRY[key]
        assert entry.display_name
        assert entry.docs_terms
        assert entry.metric_roles
        assert entry.learner_boundary


def test_registry_covers_current_protocol_controls() -> None:
    assert set(PROTOCOL_BASELINE_KEYS) <= set(BASELINE_REGISTRY)
    for key in PROTOCOL_BASELINE_KEYS:
        assert BASELINE_REGISTRY[key].category == "repo_protocol_baseline"


def test_external_baseline_entries_have_github_clone_targets() -> None:
    external_entries = [
        entry
        for entry in BASELINE_REGISTRY.values()
        if "external" in entry.implementation_status or entry.external_repositories
    ]
    assert external_entries
    for entry in external_entries:
        if entry.implementation_status == "google_dataset_pathway_only":
            continue
        assert entry.external_repositories, entry.key
        for repo in entry.external_repositories:
            assert repo.url.startswith("https://github.com/"), (entry.key, repo.url)
            assert repo.clone_path.startswith("external/baselines/"), (entry.key, repo.clone_path)


def test_native_local_references_import_modules() -> None:
    for entry in BASELINE_REGISTRY.values():
        for reference in entry.local_references:
            module_name, _, _symbol = reference.partition(":")
            module = importlib.import_module(module_name)
            assert hasattr(module, _symbol), reference


def test_registry_audit_reports_clone_state_without_requiring_network(tmp_path: Path) -> None:
    audit = baseline_registry_audit(repo_root=Path.cwd())
    assert audit["schema"] == "scope_static_baseline_registry_audit_v1"
    assert audit["coverage"]["docs_coverage_passed"] is True
    assert audit["coverage"]["protocol_coverage_passed"] is True
    assert audit["external_repositories"]

    written = write_baseline_registry_audit(tmp_path, repo_root=Path.cwd())
    assert written["coverage"]["docs_coverage_passed"] is True
    assert (tmp_path / "baseline_registry_audit.json").exists()
    assert (tmp_path / "baseline_registry_summary.md").exists()
