from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


ROOT = Path(__file__).resolve().parents[1]
WORKER_COMMON = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "gcapeps_finite_memory_worker_common.py"
)
FORK_PYTHON = (
    ROOT
    / "external"
    / "forks"
    / "quimb-gcapeps"
    / ".pixi"
    / "envs"
    / "testpymid"
    / "bin"
    / "python"
)


def _load_worker_common():
    name = "_test_gcapeps_native_ownership_worker_common"
    spec = importlib.util.spec_from_file_location(name, WORKER_COMMON)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _native_circuit():
    import quimb.tensor as qtn

    if not hasattr(qtn, "CircuitPEPSSimpleUpdate"):
        pytest.skip("current interpreter does not expose the Quimb fork")
    return qtn.CircuitPEPSSimpleUpdate(
        N=2,
        edges=((0, 1),),
        max_bond=2,
        cutoff=0.0,
        renorm=False,
        gauge_smudge=1.0e-12,
        equilibrate_every=None,
        gate_opts={
            "cutoff_mode": "rel",
            "method": "svd",
            "absorb": None,
            "power": 1.0,
        },
        dtype="complex128",
    )


def test_native_execution_candidate_is_accounted_as_owned_carrier_root():
    worker = _load_worker_common()
    circuit = _native_circuit()
    inventory = worker._GCRootInventory(engine=object())

    inventory.add_root(circuit, "native_execution_candidate")

    expected_arrays = {
        id(tensor.data) for tensor in circuit._psi.tensors
    }
    assert {id(array) for array in inventory.carrier_arrays} == (
        expected_arrays
    )
    assert inventory.ledger_payloads == []
    assert inventory.loose_arrays == []


def _run_fork_ownership_probe():
    if not FORK_PYTHON.exists():
        pytest.skip("pinned Quimb-fork interpreter is unavailable")
    code = textwrap.dedent(
        f"""
        import importlib.util
        import json
        import sys

        import numpy as np
        import quimb.tensor as qtn
        from quimb.experimental.gcapeps import (
            QuimbPEPSCarrier,
            QubitPauliWord,
        )

        worker_path = {str(WORKER_COMMON)!r}
        spec = importlib.util.spec_from_file_location(
            "_native_ownership_worker_common",
            worker_path,
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load parent worker common")
        worker = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = worker
        spec.loader.exec_module(worker)


        def run(evidence):
            circuit = qtn.CircuitPEPSSimpleUpdate(
                N=2,
                edges=((0, 1),),
                max_bond=2,
                cutoff=0.0,
                renorm=False,
                gauge_smudge=1.0e-12,
                equilibrate_every=None,
                gate_opts={{
                    "cutoff_mode": "rel",
                    "method": "svd",
                    "absorb": None,
                    "power": 1.0,
                }},
                dtype="complex128",
            )
            carrier = QuimbPEPSCarrier(
                circuit,
                pauli_rotation_strategy="native_simple_update",
                compression_evidence=evidence,
            )
            rows = []

            def sample(event, roots, metadata):
                inventory = worker._GCRootInventory(engine=object())
                for root, role in zip(roots, metadata.root_roles):
                    inventory.add_root(root, role)
                rows.append(
                    {{
                        "event": event,
                        "checkpoint": metadata.checkpoint,
                        "scope": metadata.scope,
                        "evidence_only": metadata.evidence_only,
                        "root_roles": list(metadata.root_roles),
                    }}
                )

            carrier.apply_pauli_rotation(
                QubitPauliWord.from_labels("ZZ"),
                np.float64(np.pi / 7.0),
                ownership_callback=sample,
            )
            return rows


        print(
            json.dumps(
                {{"evidence_off": run(False), "evidence_on": run(True)}},
                sort_keys=True,
            )
        )
        """
    )
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    completed = subprocess.run(
        (str(FORK_PYTHON), "-I", "-c", code),
        cwd=ROOT,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=60.0,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    return json.loads(completed.stdout)


def test_real_native_callback_roles_are_accepted_by_parent_inventory():
    traces = _run_fork_ownership_probe()
    old_aliases = {
        "native_candidate",
        "shadow_replay_record_in_progress",
    }

    for rows in traces.values():
        assert rows
        assert all(
            old_aliases.isdisjoint(row["root_roles"]) for row in rows
        )
        inner_rows = [
            row for row in rows if row["scope"] == "carrier/native"
        ]
        assert inner_rows
        assert all(
            {
                "carrier_candidate",
                "native_execution_candidate",
            }.issubset(row["root_roles"])
            for row in inner_rows
        )

    off_roles = {
        role
        for row in traces["evidence_off"]
        for role in row["root_roles"]
    }
    on_roles = {
        role
        for row in traces["evidence_on"]
        for role in row["root_roles"]
    }
    shadow_roles = {
        "evidence_shadow",
        "shadow_replay_ledger_in_progress",
    }
    assert off_roles.isdisjoint(shadow_roles)
    assert shadow_roles.issubset(on_roles)
    assert all(
        row["evidence_only"] is True
        for rows in traces.values()
        for row in rows
        if not shadow_roles.isdisjoint(row["root_roles"])
    )
