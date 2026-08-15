"""Schema-dispatched fixture validation in the finite-memory worker commons.

Both lanes' ``validate_fixture`` must route a ``fixture.v1`` payload to the
v1 emitter and a ``fixture.v2`` payload to the v2 emitter, and reject every
other schema -- future versions, the P2 arm schemas, missing or non-string
schema fields -- without fallback.  A cross-schema relabel (v1 content
carrying the v2 string, or the reverse) must be rejected by the owning
emitter's byte-identical deterministic-reconstruction check.

All fixtures built here are CALIBRATION cells; no held-out fixture is ever
materialized by this file.
"""

from __future__ import annotations

import copy
import functools
import importlib.util
from pathlib import Path
import sys

import pytest


REPO = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO / "scripts" / "external_baselines"
WORKER_COMMON_NAMES = (
    "gcapeps_finite_memory_worker_common",
    "plain_quimb_finite_memory_worker_common",
)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@functools.lru_cache(maxsize=None)
def _load(name: str):
    return _load_module(
        SCRIPT_DIR / f"{name}.py", f"_schema_dispatch_test_{name}"
    )


_CALIBRATION_CELL = {
    "run_partition": "CALIBRATION",
    "width": 7,
    "rounds": 4,
    "axis_family": 3,
    "p_event_numerator": 3,
    "seed": 2,
    "gamma_index": 2,
    "run_blpensemble": False,
}


@functools.lru_cache(maxsize=None)
def _built_fixture(emitter_name: str):
    return _load(emitter_name).build_fixture(**_CALIBRATION_CELL)


@pytest.mark.parametrize("worker_name", WORKER_COMMON_NAMES)
def test_v1_fixture_routes_to_v1_owner_unchanged(worker_name: str) -> None:
    common = _load(worker_name)
    v1 = _load("emit_gcapeps_finite_memory_fixture")
    fixture = _built_fixture("emit_gcapeps_finite_memory_fixture")

    digest = common.validate_fixture(fixture)
    assert digest == fixture["result_projection_sha256"]
    assert digest == v1.validate_fixture(fixture)

    # The v1 owner still rejects drifted v1 content through the dispatch.
    corrupted = copy.deepcopy(fixture)
    corrupted["carrier_path"]["event_rows"][0]["event"] = not corrupted[
        "carrier_path"
    ]["event_rows"][0]["event"]
    with pytest.raises(ValueError, match="deterministic reconstruction"):
        common.validate_fixture(corrupted)


@pytest.mark.parametrize("worker_name", WORKER_COMMON_NAMES)
def test_v2_fixture_accepted_and_digest_matches_v2_owner(
    worker_name: str,
) -> None:
    common = _load(worker_name)
    v2 = _load("emit_gcapeps_finite_memory_fixture_v2")
    fixture = _built_fixture("emit_gcapeps_finite_memory_fixture_v2")

    digest = common.validate_fixture(fixture)
    assert digest == fixture["result_projection_sha256"]
    assert digest == v2.validate_fixture(fixture)
    # The accepted v2 payload carries the every-round checkpoint set the
    # engines materialize from ``fixture["checkpoints"]``.
    assert fixture["state_contract"]["checkpoint_policy"] == "every_round"
    assert fixture["checkpoints"] == list(
        range(fixture["parameters"]["rounds"] + 1)
    )


@pytest.mark.parametrize("worker_name", WORKER_COMMON_NAMES)
def test_future_and_unknown_schemas_rejected_without_fallback(
    worker_name: str,
) -> None:
    common = _load(worker_name)
    cx_arm = _load("emit_gcapeps_finite_memory_cx_only_arm")
    thin_arm = _load("emit_gcapeps_finite_memory_thin_only_arm")
    fixture = _built_fixture("emit_gcapeps_finite_memory_fixture_v2")

    for wrong_schema in (
        "error_coupling_simulator.external.gcapeps_finite_memory.fixture.v3",
        fixture["schema"] + ".draft",
        cx_arm.FIXTURE_SCHEMA,
        thin_arm.FIXTURE_SCHEMA,
        "",
        123,
        None,
    ):
        relabeled = copy.deepcopy(fixture)
        relabeled["schema"] = wrong_schema
        with pytest.raises(ValueError, match="unsupported fixture schema"):
            common.validate_fixture(relabeled)

    schemaless = copy.deepcopy(fixture)
    del schemaless["schema"]
    with pytest.raises(ValueError, match="unsupported fixture schema"):
        common.validate_fixture(schemaless)

    with pytest.raises(TypeError, match="fixture must be a mapping"):
        common.validate_fixture([fixture])

    # Genuine arm fixtures are not routed either: arm execution wiring is a
    # separate, later diff.
    arm_fixture = cx_arm.build_fixture(**_CALIBRATION_CELL)
    with pytest.raises(ValueError, match="unsupported fixture schema"):
        common.validate_fixture(arm_fixture)


@pytest.mark.parametrize("worker_name", WORKER_COMMON_NAMES)
def test_cross_schema_relabel_rejected_by_owning_emitter(
    worker_name: str,
) -> None:
    common = _load(worker_name)
    v1_fixture = _built_fixture("emit_gcapeps_finite_memory_fixture")
    v2_fixture = _built_fixture("emit_gcapeps_finite_memory_fixture_v2")

    v1_as_v2 = copy.deepcopy(v1_fixture)
    v1_as_v2["schema"] = v2_fixture["schema"]
    with pytest.raises(ValueError, match="deterministic reconstruction"):
        common.validate_fixture(v1_as_v2)

    v2_as_v1 = copy.deepcopy(v2_fixture)
    v2_as_v1["schema"] = v1_fixture["schema"]
    with pytest.raises(ValueError, match="deterministic reconstruction"):
        common.validate_fixture(v2_as_v1)
