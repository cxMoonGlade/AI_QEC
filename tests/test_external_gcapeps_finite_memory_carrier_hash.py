from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "gcapeps_finite_memory_carrier_hash.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("gcapeps_fm_hash", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _plain_fixture():
    tensors = {
        0: {
            "tensor": np.arange(8, dtype=np.float64)
            .astype(np.complex128)
            .reshape(2, 2, 2),
            "physical_axis": 1,
            "virtual_axes": {1: 0, 2: 2},
        },
        1: {
            "tensor": np.ones((2, 2), dtype=np.complex128),
            "physical_axis": 0,
            "virtual_axes": {0: 1},
        },
        2: {
            "tensor": np.ones((2, 2), dtype=np.complex128) * (1.0 + 1.0j),
            "physical_axis": 1,
            "virtual_axes": {0: 0},
        },
    }
    return {
        "lane": "plain",
        "site_order": (0, 1, 2),
        "graph_edges": ((0, 2), (0, 1)),
        "site_tensors": tensors,
        "gauges": {(0, 1): np.asarray([0.8, 0.2], dtype=np.float64)},
        "frame": None,
        "input_preparation_transcript_sha256": "1" * 64,
        "shared_evolution_transcript_sha256": "2" * 64,
    }


def test_hash_is_inert_to_input_axis_layout_and_graph_order():
    module = _load_module()
    fixture = _plain_fixture()
    first = module.canonical_carrier_hash(**fixture)

    changed = copy.deepcopy(fixture)
    tensor = changed["site_tensors"][0]["tensor"]
    changed["site_tensors"][0]["tensor"] = np.transpose(tensor, (1, 2, 0))
    changed["site_tensors"][0]["physical_axis"] = 0
    changed["site_tensors"][0]["virtual_axes"] = {1: 2, 2: 1}
    changed["graph_edges"] = tuple(reversed(changed["graph_edges"]))
    second = module.canonical_carrier_hash(**changed)
    assert second["sha256"] == first["sha256"]
    assert second["header"] == first["header"]


def test_hash_changes_for_tensor_gauge_presence_frame_and_transcript():
    module = _load_module()
    fixture = _plain_fixture()
    expected = module.canonical_carrier_hash(**fixture)["sha256"]

    changed = copy.deepcopy(fixture)
    changed["site_tensors"][1]["tensor"][0, 0] += 1.0
    assert module.canonical_carrier_hash(**changed)["sha256"] != expected

    changed = copy.deepcopy(fixture)
    changed["gauges"] = {}
    assert module.canonical_carrier_hash(**changed)["sha256"] != expected

    changed = copy.deepcopy(fixture)
    changed["input_preparation_transcript_sha256"] = "3" * 64
    assert module.canonical_carrier_hash(**changed)["sha256"] != expected


def test_gc_frame_is_exact_signed_tableau_surface():
    module = _load_module()
    fixture = _plain_fixture()
    fixture["lane"] = "gcapeps"
    fixture["frame"] = {
        "kind": "stim_signed_images_v1",
        "num_qubits": 3,
        "x_images": [
            {"sign": 1, "body": "XII"},
            {"sign": 1, "body": "IXI"},
            {"sign": 1, "body": "IIX"},
        ],
        "z_images": [
            {"sign": 1, "body": "ZII"},
            {"sign": 1, "body": "IZI"},
            {"sign": 1, "body": "IIZ"},
        ],
    }
    first = module.canonical_carrier_hash(**fixture)
    changed = copy.deepcopy(fixture)
    changed["frame"]["x_images"][0]["sign"] = -1
    second = module.canonical_carrier_hash(**changed)
    assert second["sha256"] != first["sha256"]

    changed = copy.deepcopy(fixture)
    changed["frame"]["x_images"][0]["sign"] = 1j
    with pytest.raises(ValueError, match="sign"):
        module.canonical_carrier_hash(**changed)


def test_wrong_precision_and_noncanonical_gauge_fail():
    module = _load_module()
    fixture = _plain_fixture()
    fixture["site_tensors"][0]["tensor"] = fixture["site_tensors"][0][
        "tensor"
    ].astype(np.complex64)
    with pytest.raises(TypeError, match="dtype"):
        module.canonical_carrier_hash(**fixture)

    fixture = _plain_fixture()
    fixture["gauges"][(0, 1)] = np.asarray([1.0, -0.1], dtype=np.float64)
    with pytest.raises(ValueError, match="nonnegative"):
        module.canonical_carrier_hash(**fixture)
