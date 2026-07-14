"""Ownership and portability gates for the XZZX dataset parser."""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import subprocess
import sys


def test_xzzx_parser_is_owned_by_active_frontend() -> None:
    active = importlib.import_module(
        "error_coupling_simulator.frontend.xzzx_parser")

    assert active.__name__ == "error_coupling_simulator.frontend.xzzx_parser"
    assert "error_coupling_simulator/frontend/xzzx_parser.py" in str(active.__file__)


def test_xzzx_default_dataset_root_uses_xdg_data_home(tmp_path: Path) -> None:
    xdg_data_home = tmp_path / "xdg-data"
    env = dict(os.environ)
    env["XDG_DATA_HOME"] = str(xdg_data_home)
    probe = (
        "from error_coupling_simulator.frontend.xzzx_parser "
        "import DEFAULT_DATASET_ROOT; print(DEFAULT_DATASET_ROOT)"
    )

    result = subprocess.run(
        [sys.executable, "-c", probe],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert Path(result.stdout.strip()) == (
        xdg_data_home
        / "error-coupling-simulator"
        / "google_105Q_surface_code_d3_d5_d7"
    )


def test_xzzx_default_paths_preserve_dataset_layout(tmp_path: Path) -> None:
    from error_coupling_simulator.frontend import xzzx_parser

    root = tmp_path / "dataset"
    r01 = xzzx_parser.default_r01_paths(dataset_root=root)
    r10 = xzzx_parser.default_r10_paths(dataset_root=root)

    assert r01 == (
        root / "d3_at_q6_7" / "X" / "r01" / "circuit_ideal.stim",
        root / "d3_at_q6_7" / "X" / "r01" / "metadata.json",
    )
    assert r10 == (
        root / "d3_at_q6_7" / "X" / "r10" / "circuit_ideal.stim",
        root / "d3_at_q6_7" / "X" / "r10" / "metadata.json",
    )


def test_xzzx_parser_data_free_verified_semantic_smoke(tmp_path: Path) -> None:
    """Exercise the real pullback/response cross-check without external data."""
    from error_coupling_simulator.frontend import xzzx_parser

    circuit_path = tmp_path / "circuit_ideal.stim"
    metadata_path = tmp_path / "metadata.json"
    circuit_path.write_text(
        """QUBIT_COORDS(0, 0) 0
QUBIT_COORDS(1, 0) 1
R 0 1
CX sweep[0] 0
H 1
CZ 0 1
H 1
M 1
M 0
OBSERVABLE_INCLUDE(0) rec[-1]
""",
        encoding="utf-8",
    )
    metadata_path.write_text(
        json.dumps({
            "data_qubit_coords": [[0, 0]],
            "meas_qubit_coords": [[1, 0]],
            "rounds": 1,
        }),
        encoding="utf-8",
    )

    schedule = xzzx_parser.parse_xzzx_circuit(
        circuit_path, metadata_path, verify=True)

    assert schedule.n_data == 1
    assert schedule.data_indices == (0,)
    assert schedule.stab_paulis() == [{0: "Z"}]
    assert schedule.logical == {0: "Z"}
    assert schedule.logical_kind == "Z"
    assert schedule.rounds == 1
    assert schedule.within_cycle_streams == ()


def test_canonical_data_probe_honors_explicit_dataset_root(
    monkeypatch, tmp_path: Path,
) -> None:
    from conftest import _d3_paths

    root = tmp_path / "external-data"
    monkeypatch.setenv("QEC_TWIN_D3_DATA", str(root))

    paths = _d3_paths()

    assert paths == {
        "r01_circ": root / "d3_at_q6_7" / "X" / "r01" / "circuit_ideal.stim",
        "r01_meta": root / "d3_at_q6_7" / "X" / "r01" / "metadata.json",
        "r10_circ": root / "d3_at_q6_7" / "X" / "r10" / "circuit_ideal.stim",
        "r10_meta": root / "d3_at_q6_7" / "X" / "r10" / "metadata.json",
    }
