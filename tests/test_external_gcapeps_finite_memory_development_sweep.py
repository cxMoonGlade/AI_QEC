from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "gcapeps_finite_memory_development_sweep.py"
)
FIXTURE = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "emit_gcapeps_finite_memory_fixture.py"
)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def sweep():
    return _load(SCRIPT, "_test_gcapeps_fm_development_sweep")


@pytest.fixture(scope="module")
def fixture_owner():
    return _load(FIXTURE, "_test_gcapeps_fm_development_fixture")


@pytest.mark.parametrize(("rounds_star", "count"), ((4, 11), (6, 12), (12, 12)))
def test_plan_exactly_matches_frozen_cell_union(
    sweep, fixture_owner, rounds_star, count
):
    plan = sweep.build_development_plan(
        gamma_index=2,
        rounds_star=rounds_star,
    )
    assert plan["run_partition"] == "DEVELOPMENT_SWEEP"
    assert plan["formal_claim_eligible"] is False
    assert plan["is_heldout_evidence"] is False
    assert plan["transport_equivalent_to_B_CAL_or_B_HELD"] is False
    assert len(plan["cells"]) == count
    assert [row["cell"] for row in plan["cells"]] == [
        row["cell"] for row in fixture_owner.build_heldout_cells(rounds_star)
    ]
    assert [row["slice_membership"] for row in plan["cells"]] == [
        row["slice_membership"]
        for row in fixture_owner.build_heldout_cells(rounds_star)
    ]


def test_each_cell_mirrors_exact_warmup_and_measured_order(sweep):
    plan = sweep.build_development_plan(gamma_index=0, rounds_star=6)
    for cell in plan["cells"]:
        launches = cell["launches"]
        assert len(launches) == 15
        assert [row["role"] for row in launches[:5]] == [
            "dense_reference",
            "plain_evidence",
            "plain_evidence",
            "gcapeps_evidence",
            "gcapeps_evidence",
        ]
        assert [
            (row["role"], row["sample_kind"], row["sample_index"])
            for row in launches[5:13]
        ] == [
            ("plain_performance", "warmup", None),
            ("gcapeps_performance", "warmup", None),
            ("plain_performance", "measured", 0),
            ("gcapeps_performance", "measured", 0),
            ("gcapeps_performance", "measured", 1),
            ("plain_performance", "measured", 1),
            ("plain_performance", "measured", 2),
            ("gcapeps_performance", "measured", 2),
        ]
        assert [row["role"] for row in launches[-2:]] == [
            "sdim_computation",
            "terminal_comparator",
        ]


def test_plan_validator_rejects_claim_promotion(sweep):
    plan = sweep.build_development_plan(gamma_index=0, rounds_star=4)
    promoted = dict(plan)
    promoted["formal_claim_eligible"] = True
    with pytest.raises(ValueError, match="boundary"):
        sweep.validate_development_plan(promoted)


@pytest.mark.parametrize(
    "mutation",
    ("core_sha", "core_length", "trailer_schema", "timing_schema", "rss"),
)
def test_worker_trailer_validator_recomputes_core_binding_and_schema(
    sweep,
    mutation,
):
    core_bytes = b'{"bounded":"core"}'
    trailer = {
        "schema": sweep.TRAILER_SCHEMA,
        "core_byte_length": len(core_bytes),
        "core_sha256": hashlib.sha256(core_bytes).hexdigest(),
        "ru_maxrss_raw": 10,
        "ru_maxrss_units": "KiB_on_linux",
        "sample_scope": "post_worker_root_pre_trailer",
        "timing": {"schema": sweep.TIMING_SCHEMA},
    }
    sweep.validate_worker_trailer(trailer, core_bytes=core_bytes)

    corrupted = {
        **trailer,
        "timing": dict(trailer["timing"]),
    }
    if mutation == "core_sha":
        corrupted["core_sha256"] = "0" * 64
    elif mutation == "core_length":
        corrupted["core_byte_length"] += 1
    elif mutation == "trailer_schema":
        corrupted["schema"] += ".drift"
    elif mutation == "timing_schema":
        corrupted["timing"]["schema"] += ".drift"
    else:
        corrupted["ru_maxrss_raw"] = True
    with pytest.raises(ValueError):
        sweep.validate_worker_trailer(corrupted, core_bytes=core_bytes)
