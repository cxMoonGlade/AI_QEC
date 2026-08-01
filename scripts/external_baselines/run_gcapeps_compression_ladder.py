#!/usr/bin/env python3
"""Registered four-arm compression-ladder runner on the GCAPEPS w7 r4 cells.

Governing preregistration (frozen; read it in full, including both errata and
amendment 2):
  docs/simulator_validation/GCAPEPS_COMPRESSION_LADDER_FOUR_ARM_PREREG_2026-08-01.md
This script is the committed runner required by amendment 2 item 2 of that
preregistration.  It is the bit-identical promotion of the two independently
verified development harnesses

  .scratch/gcapeps-batched-pepo/runs/dev_ab_harness.py   (arms A and B)
  .scratch/gcapeps-batched-pepo/runs/dev_cd_harness.py   (arms C and D)

reorganized, not rewritten: every frozen constant, the thread envelope, the
operation grouping, the plan phase, the dense oracle, the state phase, the
compressor disciplines, the cold-start scheme, and every structural check are
carried verbatim from those harnesses, which retain no registered standing.

Arms (frozen by the preregistration):
  A  sequential two-term trees, greedy per-edge SVD, SU gauge (shipped)
  B  batched four-term event PEPO, same greedy per-edge SVD
  C  batched event PEPO, exact fused candidate, variational ALS fit
     (warm start = greedy compression of THIS ARM'S own exact fused
     candidate per erratum item 1; ``--cold-start`` runs the replicate
     control of amendment 2 item 3)
  D  batched event PEPO, exact fused candidate, environment-weighted
     l2bp compression (``tensor_network_ag_compress(method='l2bp')``)

Registered cells (amendment 2 item 1): w7 r4 gamma-index-2 CALIBRATION cells
at seeds 0, 1, 3 (FRESH), inputs 1 and 2.  Seed 2 carries no registered
standing and is accepted only in ``--mode replicate`` (DEVELOPMENT-REPLICATE
context).  Out-of-amendment cells are refused.

Provenance stamps (amendment 2 item 2): every output payload records the
main-repository HEAD commit, the fork commit, the preregistration file sha256
computed at runtime, this runner's own source sha256, the fork pixi lock
hash, and the interpreter version.  A dirty fork tree is refused outright; in
registered mode a dirty load-bearing main-repository surface is refused too.

Run under the fork pixi interpreter:
  external/forks/quimb-gcapeps/.pixi/envs/testpymid/bin/python \
      scripts/external_baselines/run_gcapeps_compression_ladder.py \
      --cell s0-g2-r4 --input 1 --arm A --mode registered

Preconditions (all printed, all fatal on failure):
  * interpreter is the fork pixi environment and quimb resolves to the fork;
  * fork tree is clean (``git status --porcelain --untracked-files=all``;
    the gitignored ``.pixi`` environment is intentionally not counted — it
    is the executing environment itself and is pinned by the lock hash);
  * the preregistration file exists and hashes;
  * the cell is inside amendment 2 for the requested mode;
  * the built fixture hash equals the committed per-seed expectation;
  * no scientific module is imported before the thread envelope is set.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[2]
FORK = REPO / "external/forks/quimb-gcapeps"
FORK_PIXI_LOCK = FORK / "pixi.lock"
PREREG_RELATIVE = (
    "docs/simulator_validation/"
    "GCAPEPS_COMPRESSION_LADDER_FOUR_ARM_PREREG_2026-08-01.md"
)
PREREG = REPO / PREREG_RELATIVE
RUNNER_RELATIVE = "scripts/external_baselines/run_gcapeps_compression_ladder.py"

SCHEMA = (
    "error_coupling_simulator.external."
    "gcapeps_compression_ladder.registered_runner.v1"
)

REGISTERED_LABEL = (
    "REGISTERED four-arm compression-ladder cell (amendment 2 item 1); "
    "headline PROVISIONAL until the registered comparison is assembled"
)
REPLICATE_LABEL = (
    "DEVELOPMENT-REPLICATE context only (seed 2); no registered standing "
    "(amendment 2 item 1)"
)

# Amendment 2 item 1: the registered comparison runs the w7 r4 gamma-index-2
# CALIBRATION cells at seeds 0/1/3 (FRESH); seed 2 is re-executed as
# DEVELOPMENT-REPLICATE context only.
REGISTERED_SEEDS = (0, 1, 3)
REPLICATE_SEEDS = (2,)
CELL_GAMMA_INDEX = 2
CELL_ROUNDS = 4
CELL_WIDTH = 7
CELL_AXIS_FAMILY = 3
CELL_P_EVENT_NUMERATOR = 3
CELL_RUN_PARTITION = "CALIBRATION"

# Per-seed fixture-hash expectations, copied from the committed
# REGISTERED_TRAJECTORY_FIXTURES table in gcapeps_native_thread_worker.py.
EXPECTED_FIXTURE_HASHES = {
    0: "18ab72ff38a1689a64499f20a571ff7bbb0e3633ab64c86ff962131a8481adc4",
    1: "d28e6b885f651d57edb1ad54e970f645434757b97f12820333ff718a3d9b14c1",
    2: "4a2abe4d32c15af833d849a62b55c45a3cb23f79383976352efaf02e1f91a463",
    3: "62b57ccab47dcf338bbc9189433db453c55eb3fe78cce5d66f5c1991b6b144aa",
}

# Frozen compressor parameters (prereg §0 plus erratum item 3; verbatim from
# the verified dev_cd_harness).
FROZEN_C = {
    "max_iterations": 40,  # passed to fit_ as steps (API name deviation)
    "tol": 1.0e-10,
    "method": "als",
    "enforce_pos": True,  # API-forced: default dense solve is singular
    "contract_optimize": "greedy",
}
FROZEN_D = {
    "max_bond": 32,
    "method": "l2bp",
    "max_iterations": 1000,
    "tol": 5.0e-6,
    # disclosed wrapper defaults at this fork revision:
    "cutoff_wrapper_default": 1.0e-10,
    "cutoff_mode_default": "rsum2",
    "damping_default": 0.0,
    "update_default": "sequential",
}
CAP = 32
I1_TOLERANCE = 1.0e-12
COLD_SEED_BASE = 20260801

THREAD_VARIABLES = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "BLIS_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "OMP_THREAD_LIMIT",
    "NUMBA_NUM_THREADS",
    "QUIMB_NUM_THREAD_WORKERS",
)

# Main-repository surfaces whose dirtiness invalidates a registered stamp.
LOAD_BEARING_PREFIXES = (
    "scripts/external_baselines/",
    "docs/simulator_validation/",
)


def _set_thread_envelope() -> None:
    for name in THREAD_VARIABLES:
        os.environ[name] = "1"
    for name in ("QUIMB_NUM_PROCS", "QUIMB_NUM_MPI_WORKERS"):
        os.environ[name] = "1"
    for name in ("OMP_DYNAMIC", "MKL_DYNAMIC"):
        os.environ[name] = "FALSE"
    os.environ["QUIMB_NUMBA_CACHE"] = "False"
    os.environ["QUIMB_MPI_SPAWN"] = "False"
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["PYTHONHASHSEED"] = "0"
    os.environ.pop("PYTHONPATH", None)
    os.environ.pop("QUIMB_DEGENERATE_BOUNDARY", None)
    loaded = sorted(
        name
        for name in sys.modules
        if name.split(".", 1)[0] in {"numpy", "quimb", "stim"}
    )
    if loaded:
        raise RuntimeError("scientific modules loaded early: " + ",".join(loaded))


def _load_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path.resolve(strict=True))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_sibling(name: str):
    return _load_path(
        f"_gcapeps_ladder_{name}",
        Path(__file__).resolve(strict=True).with_name(f"{name}.py"),
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _group_operations(operations):
    """Yield ('clifford', op) rows and ('event', [ops...]) rows in order."""

    buffer = []
    for operation in operations:
        if operation["operation_class"] == "collision_rotation":
            if buffer and (
                buffer[-1]["event_row_index"] != operation["event_row_index"]
            ):
                yield ("event", buffer)
                buffer = []
            buffer.append(operation)
            continue
        if buffer:
            yield ("event", buffer)
            buffer = []
        yield ("clifford", operation)
    if buffer:
        yield ("event", buffer)


# ======================================================================
# provenance stamps (amendment 2 item 2)
# ======================================================================


def collect_provenance_stamps(mode: str) -> dict:
    """Collect the frozen stamp set; refuse invalid provenance outright."""

    executable = Path(sys.executable).resolve()
    pixi_root = (FORK / ".pixi").resolve()
    if pixi_root not in executable.parents:
        raise RuntimeError(
            "runner must execute under the fork pixi interpreter "
            f"({pixi_root}/envs/testpymid/bin/python); got {executable}"
        )

    fork_status = _run_git(
        FORK, "status", "--porcelain", "--untracked-files=all"
    )
    if fork_status:
        raise RuntimeError(
            "fork tree is dirty; registered/replicate execution is refused:\n"
            + fork_status
        )
    fork_commit = _run_git(FORK, "rev-parse", "HEAD")

    main_head = _run_git(REPO, "rev-parse", "HEAD")
    main_status = _run_git(
        REPO, "status", "--porcelain", "--untracked-files=all"
    )
    load_bearing_dirty = [
        line
        for line in main_status.splitlines()
        if line[3:].startswith(LOAD_BEARING_PREFIXES)
    ]
    if mode == "registered" and load_bearing_dirty:
        raise RuntimeError(
            "registered mode refuses a dirty load-bearing main-repository "
            "surface (the HEAD stamp would not describe the executed "
            "code):\n" + "\n".join(load_bearing_dirty)
        )

    runner_path = Path(__file__).resolve(strict=True)
    loaded_sources = {}
    for name in (
        "emit_gcapeps_finite_memory_fixture",
        "gcapeps_finite_memory_engine",
        "gcapeps_finite_memory_dense_reference",
        "gcapeps_finite_memory_scale_balance",
    ):
        sibling = runner_path.with_name(f"{name}.py")
        if sibling.exists():
            loaded_sources[name] = _sha256_file(sibling)

    stamps = {
        "main_repository_head_commit": main_head,
        "main_repository_load_bearing_dirty": load_bearing_dirty,
        "fork_commit": fork_commit,
        "fork_status_clean": True,
        "preregistration_path": PREREG_RELATIVE,
        "preregistration_sha256": _sha256_file(PREREG),
        "runner_path": RUNNER_RELATIVE,
        "runner_source_sha256": _sha256_file(runner_path),
        "fork_pixi_lock_sha256": _sha256_file(FORK_PIXI_LOCK),
        "interpreter_version": sys.version,
        "interpreter_executable": str(executable),
        "loaded_source_sha256": loaded_sources,
        "collected_utc": datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(),
    }
    return stamps


# ======================================================================
# cell toolkit (dev lineage: dev_cd_harness.Toolkit, generalized to a
# parameterized cell and to the arm-A carrier construction)
# ======================================================================


class CellToolkit:
    """Shared modules and fixture, loaded once after the thread envelope."""

    def __init__(self, *, seed: int, gamma_index: int, rounds: int):
        import numpy as np

        self.np = np
        self.fixture_owner = _load_sibling("emit_gcapeps_finite_memory_fixture")
        self.engine = _load_sibling("gcapeps_finite_memory_engine")
        self.dense_ref = _load_sibling("gcapeps_finite_memory_dense_reference")
        import quimb
        import quimb.experimental.gcapeps as gc
        from quimb.experimental.gcapeps.pepo import (
            lower_pauli_sum_into_raw_peps,
        )
        from quimb.experimental.gcapeps.routing import (
            deterministic_routing_tree,
        )
        from quimb.tensor.tnag.compress import tensor_network_ag_compress

        quimb_root = Path(quimb.__file__).resolve()
        if FORK.resolve() not in quimb_root.parents:
            raise RuntimeError(
                f"quimb does not resolve to the fork tree: {quimb_root}"
            )
        if CAP != self.engine.SPLIT_POLICY["max_bond"]:
            raise RuntimeError("frozen CAP disagrees with GC split policy")

        self.gc = gc
        self.lower_pauli_sum_into_raw_peps = lower_pauli_sum_into_raw_peps
        self.deterministic_routing_tree = deterministic_routing_tree
        self.tensor_network_ag_compress = tensor_network_ag_compress

        self.fixture = self.fixture_owner.build_fixture(
            run_partition=CELL_RUN_PARTITION,
            width=CELL_WIDTH,
            rounds=rounds,
            axis_family=CELL_AXIS_FAMILY,
            p_event_numerator=CELL_P_EVENT_NUMERATOR,
            seed=seed,
            gamma_index=gamma_index,
            run_blpensemble=False,
        )
        self.fixture_hash = self.fixture_owner.validate_fixture(self.fixture)
        case_id = self.fixture["case_id"]
        if not case_id.startswith("calibration-"):
            raise RuntimeError(
                f"non-CALIBRATION cell refused (HELDOUT protection): {case_id}"
            )
        expected_hash = EXPECTED_FIXTURE_HASHES.get(seed)
        if expected_hash is not None and self.fixture_hash != expected_hash:
            raise RuntimeError(
                f"fixture hash for seed {seed} disagrees with the committed "
                f"expectation: {self.fixture_hash} != {expected_hash}"
            )
        self.n_qubits = self.fixture["geometry"]["n_qubits"]
        self.graph_edges = tuple(
            tuple(edge) for edge in self.fixture["geometry"]["graph_edges"]
        )
        self.sites = tuple(range(self.n_qubits))
        self.input_rows = {
            row["input_id"]: row for row in self.fixture["inputs"]
        }
        self.operations = [
            operation
            for round_row in self.fixture["carrier_path"]["round_ledger"]
            for operation in round_row["operations"]
        ]

    # ---------------- state construction (mirrors dev harnesses) ---------
    def build_state(self, input_id: int, *, batched: bool, max_bond=CAP):
        engine = self.engine
        input_row = self.input_rows[input_id]
        if self.fixture["parameters"]["max_bond"] != engine.SPLIT_POLICY[
            "max_bond"
        ]:
            raise ValueError("fixture max_bond disagrees with GC split policy")
        gate_opts = {
            "cutoff_mode": engine.SPLIT_POLICY["cutoff_mode"],
            "method": engine.SPLIT_POLICY["method"],
            "absorb": engine.SPLIT_POLICY["absorb"],
            "power": engine.SPLIT_POLICY["power"],
            "smudge_mode": engine.SPLIT_POLICY["smudge_mode"],
            "degenerate_boundary": "trim_cluster",
        }
        circuit = engine.qtn.CircuitPEPSSimpleUpdate(
            N=self.n_qubits,
            edges=self.graph_edges,
            max_bond=max_bond,
            cutoff=engine.SPLIT_POLICY["cutoff"],
            renorm=engine.SPLIT_POLICY["renorm"],
            gauge_smudge=engine.SPLIT_POLICY["smudge"],
            equilibrate_every=None,
            gate_opts=gate_opts,
            dtype="complex128",
        )
        if circuit.gate_opts.get("degenerate_boundary") != "trim_cluster":
            raise RuntimeError("degenerate_boundary was not retained")
        if any(input_row["gc_residual_initial_bits"]):
            raise ValueError("GC residual initialization must be all zero")
        frame = self.gc.StimCliffordFrame(self.n_qubits)
        transcript = []
        for operation in input_row["gc_frame_preparation_gates"]:
            frame.apply_clifford(engine._stim_circuit(operation))
            transcript.append(
                {
                    "gate_kind": operation["gate_kind"],
                    "targets": list(operation["targets"]),
                }
            )
        state_obj = self.gc.GCAPEPSState.from_quimb(
            frame,
            circuit,
            site_order=self.sites,
            contraction_optimize="greedy",
            pauli_rotation_strategy="exact_tree_then_native_compress",
            compression_evidence=False,
            batched_event_pepo="event_sum" if batched else None,
        )
        engine._validate_array_precision(state_obj._carrier._circuit)
        state_kwargs = {
            "fixture": self.fixture,
            "input_id": input_id,
            "state": state_obj,
            "physical_frame_transcript": transcript,
            "pullback_rows": [],
            "algorithm_ledger": [],
            "max_exact_precompression_bond": 1,
            "max_committed_bond": 1,
        }
        if "scale_rebalance_ledger" in engine.GCState.__dataclass_fields__:
            state_kwargs["scale_rebalance_ledger"] = []
        return engine.GCState(**state_kwargs)

    def maybe_rebalance_completed_round(self, state, round_row) -> None:
        """Round-boundary scale-rebalance hook, mirrored from the dev
        harness loop.  Guarded so the runner also loads against an engine
        without the hook (it never triggered on the verified dev runs and
        is structurally idle on gauge-free C/D states)."""

        if not hasattr(state, "needs_completed_round_scale_rebalance"):
            return
        if state.needs_completed_round_scale_rebalance():
            state.rebalance_completed_round(
                round_index=round_row["round_index"],
                last_operation_index=round_row["operations"][-1][
                    "operation_index"
                ],
            )

    # ---------------- plan phase (frame-only, BEFORE any state run) ------
    def plan_events(self, input_id: int, *, include_individual: bool):
        engine = self.engine
        gc = self.gc
        plan_frame = gc.StimCliffordFrame(self.n_qubits)
        for operation in self.input_rows[input_id][
            "gc_frame_preparation_gates"
        ]:
            plan_frame.apply_clifford(engine._stim_circuit(operation))
        rows = []
        for kind, payload in _group_operations(self.operations):
            if kind == "clifford":
                plan_frame.apply_clifford(engine._stim_circuit(payload))
                continue
            words = tuple(
                engine.QubitPauliWord.from_labels(op["physical_pauli_body"])
                for op in payload
            )
            angles = tuple(
                float.fromhex(op["theta_float64_hex"]) for op in payload
            )
            expansion = gc.expand_pauli_rotation_product(words, angles)
            pulled = gc.CoherentPauliSum(
                tuple(
                    gc.CoherentPauliTerm(
                        term.coefficient,
                        plan_frame.pullback_pauli(term.word),
                    )
                    for term in expansion.operator.terms
                )
            )
            union_tree = self.deterministic_routing_tree(
                sites=self.sites,
                graph_edges=self.graph_edges,
                terminals=tuple(
                    self.sites[q] for q in pulled.dependence_set
                ),
            )
            row = {
                "event_row_index": payload[0]["event_row_index"],
                "round_index": payload[0]["round_index"],
                "n_axes": len(payload),
                "r": pulled.active_term_count,
                "union_tree_edges": len(union_tree.edges),
            }
            if include_individual:
                individual_edges = []
                for word in words:
                    pulled_word = plan_frame.pullback_pauli(word)
                    tree = self.deterministic_routing_tree(
                        sites=self.sites,
                        graph_edges=self.graph_edges,
                        terminals=tuple(
                            self.sites[q] for q in pulled_word.support
                        ),
                    )
                    individual_edges.append(len(tree.edges))
                row["union_dependence"] = list(pulled.dependence_set)
                row["individual_tree_edges"] = individual_edges
                row["batched_doublings"] = 2 * len(union_tree.edges)
                row["sequential_doublings"] = int(sum(individual_edges))
            rows.append(row)
        return rows

    # ---------------- dense oracle (numpy-only lineage) ------------------
    def dense_checkpoints(self, input_id: int):
        np = self.np
        dense_ref = self.dense_ref
        dense_state = np.zeros(1 << self.n_qubits, dtype=np.complex128)
        dense_state[0] = 1.0
        for operation in self.input_rows[input_id][
            "gc_frame_preparation_gates"
        ]:
            kind = operation["gate_kind"]
            matrix = (
                dense_ref.cx_matrix()
                if kind == "CX"
                else dense_ref.one_qubit_matrix(kind)
            )
            dense_state = dense_ref.apply_gate_q0_msb(
                dense_state,
                matrix,
                operation["targets"],
                num_qubits=self.n_qubits,
            )
        checkpoints = {}
        for round_row in self.fixture["carrier_path"]["round_ledger"]:
            for operation in round_row["operations"]:
                if operation["operation_class"] == "collision_rotation":
                    matrix = dense_ref.pauli_rotation_matrix(
                        operation["axis"],
                        float.fromhex(operation["theta_float64_hex"]),
                    )
                elif operation["gate_kind"] == "CX":
                    matrix = dense_ref.cx_matrix()
                else:
                    matrix = dense_ref.one_qubit_matrix(
                        operation["gate_kind"]
                    )
                dense_state = dense_ref.apply_gate_q0_msb(
                    dense_state,
                    matrix,
                    operation["targets"],
                    num_qubits=self.n_qubits,
                )
            checkpoints[round_row["round_index"]] = dense_state.copy()
        return checkpoints

    # ---------------- event algebra --------------------------------------
    def event_pulled(self, state, event_ops):
        engine = self.engine
        gc = self.gc
        words = tuple(
            engine.QubitPauliWord.from_labels(op["physical_pauli_body"])
            for op in event_ops
        )
        angles = tuple(
            float.fromhex(op["theta_float64_hex"]) for op in event_ops
        )
        expansion = gc.expand_pauli_rotation_product(words, angles)
        frame = state.state._frame
        pulled = gc.CoherentPauliSum(
            tuple(
                gc.CoherentPauliTerm(
                    term.coefficient,
                    frame.pullback_pauli(term.word),
                )
                for term in expansion.operator.terms
            )
        )
        factor_pulled = tuple(frame.pullback_pauli(word) for word in words)
        return words, angles, expansion, pulled, factor_pulled

    def word_action(self, vector, codes):
        np = self.np
        indices = np.arange(vector.size, dtype=np.int64)
        xmask = 0
        factor = np.ones(vector.size, dtype=np.complex128)
        for qubit, code in enumerate(codes):
            mask = 1 << (self.n_qubits - 1 - qubit)
            bit = (indices & mask) != 0
            if code == 1:
                xmask ^= mask
            elif code == 2:
                xmask ^= mask
                factor = factor * np.where(bit, -1.0j, 1.0j)
            elif code == 3:
                factor = factor * np.where(bit, -1.0, 1.0)
        out = np.zeros_like(vector)
        out[indices ^ xmask] = factor * vector
        return out

    def exact_reference(self, before_vector, pulled):
        np = self.np
        reference = np.zeros_like(before_vector)
        for term in pulled.require_nonzero():
            effective = term.coefficient * term.word.phase
            reference = reference + effective * self.word_action(
                before_vector, term.word.codes
            )
        return reference

    def build_exact_candidate(self, state, pulled):
        """The fork's exact-lowering seam: uncompressed fused candidate.

        Identical to the probe seam dev_ab_harness used for its per-event
        lowering validation (its I1 check).
        """

        probe = state.state._carrier.copy()
        probe_circuit = probe._circuit
        lowering = self.lower_pauli_sum_into_raw_peps(
            psi=probe_circuit._psi,
            gauges=probe_circuit.gauges,
            operator=pulled,
            site_order=probe._sites,
            graph_edges=probe_circuit.edges,
            resource_limits=probe._resource_limits,
            routed_rank_products=dict(dict(probe.routed_rank_products)),
            refactor_operator_schmidt_products=dict(
                dict(probe.refactor_operator_schmidt_products)
            ),
            float64_route_identity_gauges=True,
            convert_array=(
                probe_circuit._maybe_convert
                if probe_circuit.convert_eager
                else None
            ),
        )
        return probe, lowering

    def candidate_sha256(self, circuit) -> str:
        """Canonical byte serialization of a raw candidate.

        Bond index names are per-instance uuids, so they are canonically
        renamed by first appearance walking sites in order (index ORDER
        inside each tensor is structural and deterministic for identical
        lowering sequences); site indices keep their deterministic names.
        """

        np = self.np
        digest = hashlib.sha256()
        psi = circuit._psi
        site_inds = {psi.site_ind(site) for site in self.sites}
        canonical = {}
        for site in self.sites:
            tensor = psi[psi.site_tag(site)]
            names = []
            for index in tensor.inds:
                if index in site_inds:
                    names.append(index)
                    continue
                if index not in canonical:
                    canonical[index] = f"b{len(canonical)}"
                names.append(canonical[index])
            digest.update(
                repr((site, tuple(names), tuple(tensor.shape))).encode()
            )
            digest.update(
                np.ascontiguousarray(
                    np.asarray(tensor.data, dtype=np.complex128)
                ).tobytes()
            )
        gauge_rows = sorted(
            (canonical.get(name, name), name)
            for name in circuit.gauges
        )
        for canonical_name, name in gauge_rows:
            gauge = np.asarray(circuit.gauges[name])
            digest.update(
                repr((canonical_name, tuple(gauge.shape))).encode()
            )
            digest.update(np.ascontiguousarray(gauge).tobytes())
        return digest.hexdigest()

    # ---------------- compressors ----------------------------------------
    def greedy_committed_carrier(self, state, pulled, expansion):
        """Shipped greedy per-edge SVD path on a copy of the arm carrier."""

        carrier = state.state._carrier.copy()
        update = carrier.apply_coherent_event_sum(pulled, expansion=expansion)
        if update.strategy != "exact_tree_then_native_identity_compress":
            raise ValueError("greedy event did not use the compress strategy")
        return carrier, update

    def compress_C(self, fit_tn, target_tn, *, max_sweeps=None, tol=None):
        """Frozen arm-C discipline: shipped single-sweep ALS in an outer
        loop with the shipped stop rule, disclosing per-sweep distances."""

        max_sweeps = FROZEN_C["max_iterations"] if max_sweeps is None else max_sweeps
        tol = FROZEN_C["tol"] if tol is None else tol
        xBB = float(abs(target_tn.norm(squared=True)))
        distance_history = []
        converged = False
        sweep_seconds = 0.0
        distance_seconds = 0.0
        for _ in range(max_sweeps):
            started = time.perf_counter()
            fit_tn.fit_(
                target_tn,
                method=FROZEN_C["method"],
                steps=1,
                tol=tol,
                enforce_pos=FROZEN_C["enforce_pos"],
                contract_optimize=FROZEN_C["contract_optimize"],
                xBB=xBB,
            )
            sweep_seconds += time.perf_counter() - started
            started = time.perf_counter()
            distance = float(
                fit_tn.distance(
                    target_tn,
                    xBB=xBB,
                    method="overlap",
                    normalized=True,
                    optimize=FROZEN_C["contract_optimize"],
                )
            )
            distance_seconds += time.perf_counter() - started
            distance_history.append(distance)
            if (
                len(distance_history) >= 2
                and abs(distance_history[-1] - distance_history[-2]) < tol
            ):
                converged = True
                break
        record = {
            "compressor": "quimb fit_ ALS (shipped single-sweep updates)",
            "iterations": len(distance_history),
            "max_iterations": max_sweeps,
            "tol": tol,
            "converged": bool(converged),
            "flagged_nonconverged": bool(not converged),
            "distance_first": distance_history[0] if distance_history else None,
            "distance_final": distance_history[-1] if distance_history else None,
            "distance_history": distance_history,
            "sweep_seconds": sweep_seconds,
            "distance_seconds": distance_seconds,
        }
        return fit_tn, record

    def compress_D(self, target_tn, *, max_bond=None, max_iterations=None,
                   tol=None):
        """Frozen arm-D discipline: shipped ag-compress l2bp with info."""

        info = {}
        compressed = self.tensor_network_ag_compress(
            target_tn,
            max_bond=FROZEN_D["max_bond"] if max_bond is None else max_bond,
            method=FROZEN_D["method"],
            max_iterations=(
                FROZEN_D["max_iterations"]
                if max_iterations is None
                else max_iterations
            ),
            tol=FROZEN_D["tol"] if tol is None else tol,
            info=info,
        )
        converged = bool(info.get("converged", False))
        record = {
            "compressor": "tensor_network_ag_compress(method='l2bp')",
            "iterations": int(info.get("iterations", -1)),
            "max_iterations": (
                FROZEN_D["max_iterations"]
                if max_iterations is None
                else max_iterations
            ),
            "tol": FROZEN_D["tol"] if tol is None else tol,
            "converged": converged,
            "flagged_nonconverged": bool(not converged),
            "max_mdiff": float(info.get("max_mdiff", float("nan"))),
        }
        return compressed, record

    def cold_start_like(self, warm_tn, seed: int):
        np = self.np
        rng = np.random.default_rng(seed)
        cold = warm_tn.copy()
        for tensor in cold:
            data = rng.standard_normal(
                tensor.shape
            ) + 1.0j * rng.standard_normal(tensor.shape)
            tensor.modify(
                data=np.ascontiguousarray(data, dtype=np.complex128)
            )
        norm_cold = float(abs(cold.norm()))
        norm_warm = float(abs(warm_tn.norm()))
        if norm_cold <= 0.0 or norm_warm <= 0.0:
            raise ValueError("cold-start scaling hit a zero norm")
        scale = (norm_warm / norm_cold) ** (1.0 / cold.num_tensors)
        for tensor in cold:
            tensor.modify(
                data=np.ascontiguousarray(
                    tensor.data * scale, dtype=np.complex128
                )
            )
        return cold

    def commit_compressed(self, state, compressed_tn):
        """Commit a gauge-free compressed state into the arm's carrier,
        mirroring the shipped commit (circuit swap, epoch+1, revision+1;
        the shipped commit also resets the per-edge product maps to one,
        which they already are after every committed epoch)."""

        np = self.np
        carrier = state.state._carrier.copy()
        circuit = carrier._circuit
        for tensor in compressed_tn:
            data = np.asarray(tensor.data)
            if data.dtype != np.dtype(np.complex128):
                raise TypeError("compressed tensor left complex128")
        circuit._psi = compressed_tn
        circuit.gauges = {}
        carrier._revision += 1
        carrier._construction_epoch += 1
        self.engine._validate_array_precision(circuit)
        state.state._carrier = carrier
        return carrier

    def fidelity(self, reference, vector):
        np = self.np
        overlap = complex(np.vdot(reference, vector))
        denominator = float(
            np.real(np.vdot(reference, reference))
            * np.real(np.vdot(vector, vector))
        )
        return float(abs(overlap) ** 2 / denominator)

    # ---------------- anti-degeneracy instrument (erratum item 5) --------
    def pullback_weight_report(self, pullback_rows):
        """Pullback rows/weights emitted beside the fidelities; mean weight
        of about 2.00 is the degenerate parity/fidelity regime."""

        weights = [
            sum(1 for letter in row["pulled_back_body"] if letter != "I")
            for row in pullback_rows
        ]
        mean_weight = (
            float(sum(weights)) / float(len(weights)) if weights else None
        )
        degenerate = (
            mean_weight is not None and abs(mean_weight - 2.0) <= 0.005
        )
        return {
            "per_row_pulled_back_weight": weights,
            "mean_pulled_back_weight": mean_weight,
            "degenerate_regime_mean_weight_2": bool(degenerate),
            "note": (
                "parity/fidelity at mean pullback weight ~= 2.00 is the "
                "degenerate regime (prereg erratum item 5); rows and "
                "weights are emitted beside the fidelities, not only "
                "their sha"
            ),
        }


# ======================================================================
# arms A and B (dev lineage: dev_ab_harness.main state phase, verbatim)
# ======================================================================


def run_arm_ab(tk: CellToolkit, arm: str, input_id: int, tag: str):
    np = tk.np
    engine = tk.engine
    batched = arm == "B"
    # The stored, verified dev artifacts ran the batched arm with per-event
    # lowering validation ON and the sequential arm with it OFF; the
    # validation is probe-only (never mutates the carrier).
    validate_lowering = batched
    n_qubits = tk.n_qubits
    print(f"[{tag}] fixture {tk.fixture['case_id']} {tk.fixture_hash}", flush=True)

    plan_events = tk.plan_events(input_id, include_individual=True)
    plan_summary = {
        "n_events": len(plan_events),
        "r_distribution": {
            str(r): sum(1 for e in plan_events if e["r"] == r)
            for r in sorted({e["r"] for e in plan_events})
        },
        "batched_split_total": sum(e["union_tree_edges"] for e in plan_events),
        "sequential_split_total": sum(
            sum(e["individual_tree_edges"]) for e in plan_events
        ),
        "batched_doublings_total": sum(
            e["batched_doublings"] for e in plan_events
        ),
        "sequential_doublings_total": sum(
            e["sequential_doublings"] for e in plan_events
        ),
        "router": "shipped deterministic_routing_tree",
    }
    print(f"[{tag}] plan: {json.dumps(plan_summary)}", flush=True)

    dense_checkpoints = tk.dense_checkpoints(input_id)
    state = tk.build_state(input_id, batched=batched)

    physical_vectors = {}
    event_measurements = []
    lowering_validation = []
    apply_seconds = 0.0
    wall_start = time.perf_counter()
    operation_count = 0
    event_index = 0

    def _apply_batched_event(event_ops):
        nonlocal apply_seconds, event_index
        words = tuple(
            engine.QubitPauliWord.from_labels(op["physical_pauli_body"])
            for op in event_ops
        )
        angles = tuple(
            float.fromhex(op["theta_float64_hex"]) for op in event_ops
        )
        requests = [state._request_for_operation(op) for op in event_ops]
        if validate_lowering and len(event_ops) > 1:
            expansion = tk.gc.expand_pauli_rotation_product(words, angles)
            pulled = tk.gc.CoherentPauliSum(
                tuple(
                    tk.gc.CoherentPauliTerm(
                        term.coefficient,
                        state.state._frame.pullback_pauli(term.word),
                    )
                    for term in expansion.operator.terms
                )
            )
            before_vector = state.residual_state_vector()
            probe, _ = tk.build_exact_candidate(state, pulled)
            lowered_vector = probe.state_vector(max_qubits=14)
            reference = tk.exact_reference(before_vector, pulled)
            error = float(np.max(np.abs(lowered_vector - reference)))
            lowering_validation.append(
                {
                    "event_index": event_index,
                    "round_index": event_ops[0]["round_index"],
                    "event_row_index": event_ops[0]["event_row_index"],
                    "max_abs_error": error,
                    "passed_1e12": bool(error <= 1e-12),
                }
            )
            del probe
        started = time.perf_counter()
        event = state.state.apply_collision_event(words, angles)
        apply_seconds += time.perf_counter() - started
        update = event.residual_update
        if update.strategy != "exact_tree_then_native_identity_compress":
            raise ValueError("batched event did not use the compress strategy")
        if len(event_ops) > 1:
            pulled_texts = event.factor_pulled_back_terms
        else:
            pulled_texts = (event.pulled_back_pauli,)
        for op, request, pulled_text in zip(
            event_ops, requests, pulled_texts
        ):
            value = engine._signed_word_text_value(
                pulled_text, num_qubits=n_qubits
            )
            state.pullback_rows.append(
                {
                    **request,
                    "physical_sign": 1,
                    "physical_body": op["physical_pauli_body"],
                    "pulled_back_sign": value["sign"],
                    "pulled_back_body": value["body"],
                }
            )
        ledger = update.tree_compression_ledger
        if ledger is None:
            raise ValueError("event omitted its compression ledger")
        exact_bonds = [
            row.exact_precompression_bond for row in ledger.split_records
        ]
        if exact_bonds:
            state.max_exact_precompression_bond = max(
                state.max_exact_precompression_bond, *exact_bonds
            )
        state.max_committed_bond = max(
            state.max_committed_bond, update.max_bond_after
        )
        plan_row = plan_events[event_index]
        if len(event_ops) > 1:
            if plan_row["event_row_index"] != event_ops[0]["event_row_index"]:
                raise ValueError("plan/state event alignment drifted")
            if len(update.routing_tree_edges) != plan_row["union_tree_edges"]:
                raise ValueError("state union tree disagrees with plan")
            if update.active_term_count != plan_row["r"]:
                raise ValueError("state term count disagrees with plan")
        event_measurements.append(
            {
                "event_index": event_index,
                "round_index": event_ops[0]["round_index"],
                "event_row_index": event_ops[0]["event_row_index"],
                "n_axes": len(event_ops),
                "r": update.active_term_count,
                "epochs": [
                    update.construction_epoch_before,
                    update.construction_epoch_after,
                ],
                "splits": len(ledger.split_records),
                "exact_bonds": exact_bonds,
                "kept_bonds": [
                    row.kept_bond_dimension for row in ledger.split_records
                ],
                "truncating_splits": sum(
                    row.kept_bond_dimension < row.exact_precompression_bond
                    for row in ledger.split_records
                ),
                "positive_splits": sum(
                    row.positive_discarded_weight
                    for row in ledger.split_records
                ),
                "discarded_weight_total": (
                    float(
                        ledger.total_discarded_squared_weight_diagnostic_only
                    )
                    if ledger.total_discarded_squared_weight_diagnostic_only
                    is not None
                    else None
                ),
                "compression_revision": ledger.compression_revision,
                "event_term_count": ledger.event_term_count,
            }
        )
        event_index += 1

    def _apply_sequential_event(event_ops):
        nonlocal apply_seconds, event_index
        splits = 0
        exact_bonds_all = []
        kept_bonds_all = []
        truncating = 0
        positive = 0
        discarded_totals = []
        epochs = []
        revisions = set()
        for op in event_ops:
            request = state._request_for_operation(op)
            physical = engine.QubitPauliWord.from_labels(
                op["physical_pauli_body"]
            )
            started = time.perf_counter()
            event = state.state.apply_pauli_rotation(
                physical, float.fromhex(op["theta_float64_hex"])
            )
            apply_seconds += time.perf_counter() - started
            update = event.residual_update
            if update.strategy != (
                "exact_tree_then_native_identity_compress"
            ):
                raise ValueError("collision did not use the compress strategy")
            value = engine._signed_word_text_value(
                event.pulled_back_pauli, num_qubits=n_qubits
            )
            state.pullback_rows.append(
                {
                    **request,
                    "physical_sign": 1,
                    "physical_body": op["physical_pauli_body"],
                    "pulled_back_sign": value["sign"],
                    "pulled_back_body": value["body"],
                }
            )
            ledger = update.tree_compression_ledger
            revisions.add(ledger.compression_revision)
            epochs.append(
                [
                    update.construction_epoch_before,
                    update.construction_epoch_after,
                ]
            )
            splits += len(ledger.split_records)
            for row in ledger.split_records:
                exact_bonds_all.append(row.exact_precompression_bond)
                kept_bonds_all.append(row.kept_bond_dimension)
                truncating += (
                    row.kept_bond_dimension < row.exact_precompression_bond
                )
                positive += row.positive_discarded_weight
            if (
                ledger.total_discarded_squared_weight_diagnostic_only
                is not None
            ):
                discarded_totals.append(
                    float(
                        ledger.total_discarded_squared_weight_diagnostic_only
                    )
                )
            if exact_bonds_all:
                state.max_exact_precompression_bond = max(
                    state.max_exact_precompression_bond, *exact_bonds_all
                )
            state.max_committed_bond = max(
                state.max_committed_bond, update.max_bond_after
            )
        event_measurements.append(
            {
                "event_index": event_index,
                "round_index": event_ops[0]["round_index"],
                "event_row_index": event_ops[0]["event_row_index"],
                "n_axes": len(event_ops),
                "r": None,
                "epochs": epochs,
                "splits": splits,
                "exact_bonds": exact_bonds_all,
                "kept_bonds": kept_bonds_all,
                "truncating_splits": truncating,
                "positive_splits": positive,
                "discarded_weight_total": (
                    float(np.sum(discarded_totals))
                    if discarded_totals
                    else None
                ),
                "compression_revision": sorted(revisions),
                "event_term_count": None,
            }
        )
        event_index += 1

    for round_row in tk.fixture["carrier_path"]["round_ledger"]:
        round_index = round_row["round_index"]
        state.advance_round(round_index)
        for kind, payload in _group_operations(round_row["operations"]):
            if kind == "clifford":
                if payload["operation_index"] != operation_count:
                    raise ValueError("operation order drifted")
                started = time.perf_counter()
                event = state.state.apply_clifford(
                    engine._stim_circuit(payload)
                )
                apply_seconds += time.perf_counter() - started
                state.physical_frame_transcript.append(
                    {
                        "gate_kind": payload["gate_kind"],
                        "targets": list(payload["targets"]),
                    }
                )
                if (
                    event.peps_gate_count_before
                    != event.peps_gate_count_after
                ):
                    raise ValueError("Clifford changed residual gate count")
                operation_count += 1
                continue
            if payload[0]["operation_index"] != operation_count:
                raise ValueError("operation order drifted")
            if batched:
                _apply_batched_event(payload)
            else:
                _apply_sequential_event(payload)
            operation_count += len(payload)
        tk.maybe_rebalance_completed_round(state, round_row)
        physical_vectors[round_index] = state.physical_state_vector()
        print(
            f"[{tag}] round {round_index} ops={operation_count} "
            f"events={event_index} "
            f"max_exact={state.max_exact_precompression_bond} "
            f"max_committed={state.max_committed_bond} "
            f"t={time.perf_counter() - wall_start:.1f}s",
            flush=True,
        )

    wall = time.perf_counter() - wall_start

    # engine-style pullback coverage check: one row per collision ordinal
    expected_pullbacks = [
        row
        for row in tk.fixture["sdim_pullback_requests"]
        if row["input_id"] == input_id
    ]
    observed_keys = [
        {key: row[key] for key in tk.fixture_owner.PULLBACK_REQUEST_KEYS}
        for row in state.pullback_rows
    ]
    if observed_keys != expected_pullbacks:
        raise ValueError("pullback rows do not exactly cover the requests")
    print(f"[{tag}] pullback coverage check passed "
          f"({len(observed_keys)} rows)", flush=True)

    fidelities = {}
    for round_index, vector in physical_vectors.items():
        fidelities[round_index] = tk.fidelity(
            dense_checkpoints[round_index], vector
        )

    payload = {
        "arm": arm,
        "dev_lineage_arm": "batched" if batched else "sequential",
        "input_id": input_id,
        "shadow_evidence": False,
        "case_id": tk.fixture["case_id"],
        "fixture_hash": tk.fixture_hash,
        "thread_count": 1,
        "policy": {
            "max_bond": engine.SPLIT_POLICY["max_bond"],
            "degenerate_boundary": "trim_cluster",
            "strategy": "exact_tree_then_native_compress",
        },
        "plan_summary": plan_summary,
        "plan_events": plan_events,
        "operation_count": operation_count,
        "event_count": event_index,
        "event_measurements": event_measurements,
        "measured": {
            "splits_total": sum(e["splits"] for e in event_measurements),
            "truncating_splits_total": sum(
                e["truncating_splits"] for e in event_measurements
            ),
            "truncation_events": sum(
                1 for e in event_measurements if e["truncating_splits"] > 0
            ),
            "positive_splits_total": sum(
                e["positive_splits"] for e in event_measurements
            ),
            "positive_events": sum(
                1 for e in event_measurements if e["positive_splits"] > 0
            ),
            "discarded_weight_grand_total_diagnostic_only": float(
                np.sum(
                    [
                        e["discarded_weight_total"]
                        for e in event_measurements
                        if e["discarded_weight_total"] is not None
                    ]
                )
            ),
        },
        "lowering_validation": {
            "enabled": bool(validate_lowering),
            "events_checked": len(lowering_validation),
            "all_passed_1e12": all(
                row["passed_1e12"] for row in lowering_validation
            )
            if lowering_validation
            else None,
            "max_abs_error_overall": max(
                (row["max_abs_error"] for row in lowering_validation),
                default=None,
            ),
            "rows": lowering_validation,
        },
        "fidelity_vs_dense_oracle": fidelities,
        "infidelity_vs_dense_oracle": {
            k: 1.0 - v for k, v in fidelities.items()
        },
        "scale_rebalance_ledger": list(
            getattr(state, "scale_rebalance_ledger", [])
        ),
        "scale_rebalance_hook_available": hasattr(
            state, "needs_completed_round_scale_rebalance"
        ),
        "max_exact_precompression_bond": state.max_exact_precompression_bond,
        "max_committed_bond": state.max_committed_bond,
        "pullback_rows_sha256": hashlib.sha256(
            json.dumps(state.pullback_rows, sort_keys=True).encode()
        ).hexdigest(),
        "pullback_rows": list(state.pullback_rows),
        "pullback_weight_report": tk.pullback_weight_report(
            state.pullback_rows
        ),
        "wall_seconds_total": wall,
        "wall_seconds_apply_loop": apply_seconds,
        "vector_sha256": {
            f"physical_r{k}": hashlib.sha256(v.tobytes()).hexdigest()
            for k, v in physical_vectors.items()
        },
    }
    return payload, physical_vectors, dense_checkpoints, fidelities, wall, apply_seconds


# ======================================================================
# arms C and D (dev lineage: dev_cd_harness.run_arm, verbatim)
# ======================================================================


def run_arm_cd(tk: CellToolkit, arm: str, input_id: int, fit_init: str, tag: str):
    np = tk.np
    engine = tk.engine
    print(f"[{tag}] fixture {tk.fixture['case_id']} {tk.fixture_hash}", flush=True)
    plan = tk.plan_events(input_id, include_individual=False)
    dense_checkpoints = tk.dense_checkpoints(input_id)
    state = tk.build_state(input_id, batched=True)

    physical_vectors = {}
    event_records = []
    i1_rows = []
    flagged_events = []
    apply_seconds = 0.0
    validation_seconds = 0.0
    wall_start = time.perf_counter()
    operation_count = 0
    event_index = 0
    event1_candidate_sha = None
    max_exact_candidate_bond = 0

    for round_row in tk.fixture["carrier_path"]["round_ledger"]:
        round_index = round_row["round_index"]
        state.advance_round(round_index)
        for kind, payload in _group_operations(round_row["operations"]):
            if kind == "clifford":
                if payload["operation_index"] != operation_count:
                    raise ValueError("operation order drifted")
                started = time.perf_counter()
                event = state.state.apply_clifford(
                    engine._stim_circuit(payload)
                )
                apply_seconds += time.perf_counter() - started
                state.physical_frame_transcript.append(
                    {
                        "gate_kind": payload["gate_kind"],
                        "targets": list(payload["targets"]),
                    }
                )
                if event.peps_gate_count_before != event.peps_gate_count_after:
                    raise ValueError("Clifford changed residual gate count")
                operation_count += 1
                continue

            if payload[0]["operation_index"] != operation_count:
                raise ValueError("operation order drifted")
            event_ops = payload
            requests = [state._request_for_operation(op) for op in event_ops]
            (
                words,
                angles,
                expansion,
                pulled,
                factor_pulled,
            ) = tk.event_pulled(state, event_ops)

            # pre-event dense state for this arm's own I1 check
            started = time.perf_counter()
            before_vector = state.residual_state_vector()
            validation_seconds += time.perf_counter() - started

            # exact fused candidate through the fork's lowering seam
            started = time.perf_counter()
            probe, lowering = tk.build_exact_candidate(state, pulled)
            apply_seconds += time.perf_counter() - started

            plan_row = plan[event_index]
            if plan_row["event_row_index"] != event_ops[0]["event_row_index"]:
                raise ValueError("plan/state event alignment drifted")
            if len(lowering.tree.edges) != plan_row["union_tree_edges"]:
                raise ValueError("state union tree disagrees with plan")
            if lowering.active_term_count != plan_row["r"]:
                raise ValueError("state term count disagrees with plan")

            candidate_bond_value = probe._circuit._psi.max_bond()
            candidate_bond = (
                1 if candidate_bond_value is None else int(candidate_bond_value)
            )
            max_exact_candidate_bond = max(
                max_exact_candidate_bond, candidate_bond
            )
            if candidate_bond > 128:
                raise ValueError(
                    f"exact fused bond {candidate_bond} exceeds the P1 bound"
                )
            if event_index == 0:
                event1_candidate_sha = tk.candidate_sha256(probe._circuit)

            # I1: per-event exact-lowering validation at 1e-12 (mandatory)
            started = time.perf_counter()
            lowered_vector = probe.state_vector(max_qubits=14)
            reference = tk.exact_reference(before_vector, pulled)
            i1_error = float(np.max(np.abs(lowered_vector - reference)))
            validation_seconds += time.perf_counter() - started
            if i1_error > I1_TOLERANCE:
                raise ValueError(
                    f"I1 exact-lowering check failed at event {event_index}: "
                    f"{i1_error}"
                )
            i1_rows.append(
                {
                    "event_index": event_index,
                    "round_index": round_index,
                    "event_row_index": event_ops[0]["event_row_index"],
                    "max_abs_error": i1_error,
                    "passed_1e12": True,
                }
            )

            # arm compression discipline
            if arm == "C":
                started = time.perf_counter()
                greedy_carrier, greedy_update = tk.greedy_committed_carrier(
                    state, pulled, expansion
                )
                warm_tn = greedy_carrier._circuit.get_psi()
                target_tn = probe._circuit.get_psi()
                if fit_init == "cold":
                    seed = COLD_SEED_BASE * 1000 + input_id * 100 + event_index
                    fit_tn = tk.cold_start_like(warm_tn, seed)
                else:
                    fit_tn = warm_tn
                compressed_tn, comp_record = tk.compress_C(fit_tn, target_tn)
                apply_seconds += time.perf_counter() - started
                comp_record["greedy_max_bond_after"] = int(
                    greedy_update.max_bond_after
                )
                comp_record["fit_init"] = fit_init
                if fit_init == "cold":
                    comp_record["cold_seed"] = seed
                del greedy_carrier
            else:
                started = time.perf_counter()
                target_tn = probe._circuit.get_psi()
                compressed_tn, comp_record = tk.compress_D(target_tn)
                apply_seconds += time.perf_counter() - started

            if comp_record["flagged_nonconverged"]:
                flagged_events.append(event_index)
                print(
                    f"[{tag}] FLAGGED non-converged compressor at event "
                    f"{event_index} (iterations="
                    f"{comp_record['iterations']})",
                    flush=True,
                )

            started = time.perf_counter()
            tk.commit_compressed(state, compressed_tn)
            apply_seconds += time.perf_counter() - started

            committed_bond_value = state.state._carrier._circuit._psi.max_bond()
            committed_bond = (
                1 if committed_bond_value is None else int(committed_bond_value)
            )
            if committed_bond > CAP:
                raise ValueError(
                    f"committed bond {committed_bond} exceeds the cap"
                )
            state.max_exact_precompression_bond = max(
                state.max_exact_precompression_bond, candidate_bond
            )
            state.max_committed_bond = max(
                state.max_committed_bond, committed_bond
            )

            for op, request, pulled_word in zip(
                event_ops, requests, factor_pulled
            ):
                value = engine._signed_word_text_value(
                    str(pulled_word), num_qubits=tk.n_qubits
                )
                state.pullback_rows.append(
                    {
                        **request,
                        "physical_sign": 1,
                        "physical_body": op["physical_pauli_body"],
                        "pulled_back_sign": value["sign"],
                        "pulled_back_body": value["body"],
                    }
                )

            event_records.append(
                {
                    "event_index": event_index,
                    "round_index": round_index,
                    "event_row_index": event_ops[0]["event_row_index"],
                    "n_axes": len(event_ops),
                    "r": int(lowering.active_term_count),
                    "union_tree_edges": len(lowering.tree.edges),
                    "exact_candidate_max_bond": candidate_bond,
                    "committed_max_bond": committed_bond,
                    "i1_max_abs_error": i1_error,
                    "compression": comp_record,
                }
            )
            operation_count += len(event_ops)
            event_index += 1
            del probe, lowering, compressed_tn

        tk.maybe_rebalance_completed_round(state, round_row)
        physical_vectors[round_index] = state.physical_state_vector()
        print(
            f"[{tag}] round {round_index} ops={operation_count} "
            f"events={event_index} "
            f"max_exact={state.max_exact_precompression_bond} "
            f"max_committed={state.max_committed_bond} "
            f"t={time.perf_counter() - wall_start:.1f}s",
            flush=True,
        )

    wall = time.perf_counter() - wall_start

    expected_pullbacks = [
        row
        for row in tk.fixture["sdim_pullback_requests"]
        if row["input_id"] == input_id
    ]
    observed_keys = [
        {key: row[key] for key in tk.fixture_owner.PULLBACK_REQUEST_KEYS}
        for row in state.pullback_rows
    ]
    if observed_keys != expected_pullbacks:
        raise ValueError("pullback rows do not exactly cover the requests")
    print(
        f"[{tag}] pullback coverage check passed ({len(observed_keys)} rows)",
        flush=True,
    )

    fidelities = {}
    for round_index, vector in physical_vectors.items():
        fidelities[round_index] = tk.fidelity(
            dense_checkpoints[round_index], vector
        )

    payload = {
        "arm": arm,
        "fit_init": fit_init if arm == "C" else None,
        "input_id": input_id,
        "case_id": tk.fixture["case_id"],
        "fixture_hash": tk.fixture_hash,
        "thread_count": 1,
        "policy": {
            "max_bond": CAP,
            "degenerate_boundary": "trim_cluster",
            "between_events": "arm B path (Cliffords via frame, shipped policy)",
            "frozen_C": FROZEN_C,
            "frozen_D": FROZEN_D,
        },
        "operation_count": operation_count,
        "event_count": event_index,
        "event1_candidate_sha256": event1_candidate_sha,
        "max_exact_candidate_bond": max_exact_candidate_bond,
        "max_committed_bond": state.max_committed_bond,
        "event_records": event_records,
        "i1_validation": {
            "events_checked": len(i1_rows),
            "all_passed_1e12": all(row["passed_1e12"] for row in i1_rows),
            "max_abs_error_overall": max(
                row["max_abs_error"] for row in i1_rows
            ),
            "rows": i1_rows,
        },
        "convergence": {
            "flagged_nonconverged_events": flagged_events,
            "n_flagged": len(flagged_events),
            "n_converged": event_index - len(flagged_events),
        },
        "initialization_sensitivity_designation": (
            "arm C is designated INITIALIZATION-SENSITIVE and its "
            "non-converged fit counts are disclosed prominently "
            "(prereg erratum item 6)"
            if arm == "C"
            else None
        ),
        "fidelity_vs_dense_oracle": fidelities,
        "infidelity_vs_dense_oracle": {
            k: 1.0 - v for k, v in fidelities.items()
        },
        "scale_rebalance_ledger": list(
            getattr(state, "scale_rebalance_ledger", [])
        ),
        "scale_rebalance_hook_available": hasattr(
            state, "needs_completed_round_scale_rebalance"
        ),
        "pullback_rows_sha256": hashlib.sha256(
            json.dumps(state.pullback_rows, sort_keys=True).encode()
        ).hexdigest(),
        "pullback_rows": list(state.pullback_rows),
        "pullback_weight_report": tk.pullback_weight_report(
            state.pullback_rows
        ),
        "wall_seconds_total": wall,
        "wall_seconds_apply_loop": apply_seconds,
        "wall_seconds_validation": validation_seconds,
        "vector_sha256": {
            f"physical_r{k}": hashlib.sha256(v.tobytes()).hexdigest()
            for k, v in physical_vectors.items()
        },
    }
    return payload, physical_vectors, dense_checkpoints, fidelities, wall, apply_seconds


# ======================================================================
# CLI
# ======================================================================


def parse_cell(text: str):
    match = re.fullmatch(r"s(\d+)-g(\d+)-r(\d+)", text)
    if match is None:
        raise argparse.ArgumentTypeError(
            "cell must look like s2-g2-r4 (seed / gamma-index / rounds)"
        )
    return {
        "seed": int(match.group(1)),
        "gamma_index": int(match.group(2)),
        "rounds": int(match.group(3)),
    }


def refuse(message: str) -> int:
    print(f"REFUSED: {message}", flush=True)
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--cell",
        type=parse_cell,
        required=True,
        help="cell spec s<seed>-g<gamma_index>-r<rounds>, e.g. s0-g2-r4",
    )
    parser.add_argument("--input", type=int, choices=(1, 2), required=True)
    parser.add_argument(
        "--arm", choices=("A", "B", "C", "D"), required=True
    )
    parser.add_argument(
        "--mode", choices=("registered", "replicate"), required=True
    )
    parser.add_argument(
        "--cold-start",
        action="store_true",
        help="arm-C cold-start replicate control (amendment 2 item 3)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSON output path (.json); complete vectors go beside it (.npz)",
    )
    args = parser.parse_args()

    cell = args.cell
    seed = cell["seed"]
    if cell["gamma_index"] != CELL_GAMMA_INDEX or cell["rounds"] != CELL_ROUNDS:
        return refuse(
            "amendment 2 registers only the w7 r4 gamma-index-2 CALIBRATION "
            f"cells; got gamma-index {cell['gamma_index']}, rounds "
            f"{cell['rounds']}"
        )
    if args.mode == "registered" and seed not in REGISTERED_SEEDS:
        return refuse(
            f"registered mode accepts seeds {REGISTERED_SEEDS} only "
            f"(amendment 2 item 1); seed {seed} was requested. Seed 2 runs "
            "only as --mode replicate (DEVELOPMENT-REPLICATE context)."
        )
    if args.mode == "replicate" and seed not in REPLICATE_SEEDS:
        return refuse(
            f"replicate mode is the seed-2 DEVELOPMENT-REPLICATE context "
            f"only (amendment 2 item 1); seed {seed} was requested."
        )
    if args.cold_start and args.arm != "C":
        return refuse("--cold-start is the arm-C replicate control only")
    if (
        args.cold_start
        and args.mode == "registered"
        and args.input != 1
    ):
        return refuse(
            "the registered cold-start control scope is input 1, round-4 "
            "comparison (amendment 2 item 3)"
        )

    _set_thread_envelope()
    print(f"preconditions: prereg {PREREG_RELATIVE}", flush=True)
    stamps = collect_provenance_stamps(args.mode)
    for key in (
        "main_repository_head_commit",
        "fork_commit",
        "preregistration_sha256",
        "runner_source_sha256",
        "fork_pixi_lock_sha256",
        "interpreter_version",
    ):
        print(f"stamp {key}: {stamps[key]}", flush=True)
    if stamps["main_repository_load_bearing_dirty"]:
        print(
            "stamp main_repository_load_bearing_dirty: "
            + json.dumps(stamps["main_repository_load_bearing_dirty"]),
            flush=True,
        )

    fit_init = "cold" if args.cold_start else "warm"
    mode_token = "registered" if args.mode == "registered" else "replicate"
    arm_token = (
        f"{args.arm}_{fit_init}" if args.arm == "C" else args.arm
    )
    tag = f"{mode_token}_s{seed}_{arm_token}_in{args.input}"

    tk = CellToolkit(
        seed=seed,
        gamma_index=cell["gamma_index"],
        rounds=cell["rounds"],
    )

    if args.arm in ("A", "B"):
        (
            payload,
            physical_vectors,
            dense_checkpoints,
            fidelities,
            wall,
            apply_seconds,
        ) = run_arm_ab(tk, args.arm, args.input, tag)
    else:
        (
            payload,
            physical_vectors,
            dense_checkpoints,
            fidelities,
            wall,
            apply_seconds,
        ) = run_arm_cd(tk, args.arm, args.input, fit_init, tag)

    payload = {
        "schema": SCHEMA,
        "mode": args.mode,
        "registered_standing": args.mode == "registered",
        "label": (
            REGISTERED_LABEL if args.mode == "registered" else REPLICATE_LABEL
        ),
        "cell": {
            "seed": seed,
            "gamma_index": cell["gamma_index"],
            "rounds": cell["rounds"],
            "width": CELL_WIDTH,
            "axis_family": CELL_AXIS_FAMILY,
            "p_event_numerator": CELL_P_EVENT_NUMERATOR,
            "run_partition": CELL_RUN_PARTITION,
            "case_id": tk.fixture["case_id"],
        },
        "provenance_stamps": stamps,
        **payload,
    }

    if args.output is None:
        out_dir = REPO / ".scratch/gcapeps-batched-pepo" / (
            "registered" if args.mode == "registered" else "replicate"
        )
        json_path = out_dir / f"ladder_{tag}.json"
    else:
        json_path = args.output
        if json_path.suffix != ".json":
            return refuse("--output must end with .json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    npz_path = json_path.with_suffix(".npz")
    np = tk.np
    np.savez(
        npz_path,
        **{f"physical_r{k}": v for k, v in physical_vectors.items()},
        **{f"dense_r{k}": v for k, v in dense_checkpoints.items()},
    )
    json_path.write_text(json.dumps(payload, indent=1, sort_keys=True))
    print(
        f"[{tag}] done wall={wall:.1f}s apply={apply_seconds:.1f}s "
        f"fidelities={ {k: round(v, 12) for k, v in fidelities.items()} } "
        f"wrote {json_path} and {npz_path}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
