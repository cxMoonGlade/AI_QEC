from __future__ import annotations

"""Parse an external d3 XZZX ``circuit_ideal.stim`` into the QutritDM Schedule.

The exact 9-data-qutrit engine
(:class:`error_coupling_simulator.carrier.exact.qutrit_dm.QutritDM`) evolves only the DATA register
and measures each stabilizer by a direct parity projection on the data density
matrix (no ancilla instantiated). This parser turns the real Google Willow XZZX
``circuit_ideal.stim`` into the data-side description that engine consumes:

  * the 9 data qutrits, mapped to engine register positions ``0..8`` in the
    metadata ``data_qubit_coords`` order;
  * the 8 stabilizer supports as ``("stab", paulis, stab_id)`` ops, where
    ``paulis : dict[data_position -> 'X' | 'Z']`` is the XZZX stabilizer support
    (compiled from the data<->ancilla CZ + ancilla M; ancilla never enter the
    register);
  * the logical observable (``OBSERVABLE_INCLUDE``), as a ``{data_position -> 'X'|'Z'}``
    dict ready for :meth:`QutritDM.set_code`.

Two input normalizations are applied at parse time:

  * **surplus qubits dropped.** The supported external *multi-round* circuit declares 20 qubit
    indices; 3 (idx 0/7/19 at r10/r13) are inert (reset-but-never-measured /
    never-gated boundary slots) and are NOT data or measure qubits. They are dropped.
    At **r01** the circuit is natively 17 qubits / 8 detectors with **zero surplus**
    (verified, ``feas_surplus_qubit_roles.py``), so the drop is a no-op there -- but
    the logic is implemented so r10/r13 parse correctly too.
  * **sweep-CX resolved to X / I.** ``CX sweep[k] q`` is a classically-controlled
    data initialization (the sweep bit decides X-or-I on qubit ``q``; dataset note
    (b) "sweep-bit semantics"), NOT a 2-qutrit entangler. The ideal (noiseless)
    circuit corresponds to the all-zero sweep word, which resolves every sweep-CX to
    the IDENTITY; the parser records the resolved per-data X/I pattern for a chosen
    sweep word (default all-zero) so the engine's logical-``|m>`` preparation is
    consistent with the data-init the circuit would apply.

Stabilizer extraction is **rigorous, not pattern-matched.** Each stabilizer is the
Heisenberg pullback ``U^dag Z_anc U`` of the ancilla's measured ``Z`` operator
through the round's Clifford ``U`` (H / CZ / X), restricted to the data qutrits -- an
exact operator identity (Method 1). :func:`extract_stabilizers` independently
cross-checks it against a deterministic single-Pauli-error -> ancilla-flip response
and refuses to return a schedule if the two disagree. On the
real ``d3_at_q6_7`` X-basis r01 patch the result is the textbook rotated d3 surface
code in the XZZX gauge: 4 X-type + 4 Z-type stabilizers (weight 2 on the boundary,
weight 4 in the bulk) and a weight-3 logical Z.

This module imports ``stim`` (parse only) and is pure CPU bookkeeping -- it builds
the *description* the GPU engine consumes; it runs no density-matrix evolution.
"""

import itertools
import os
from dataclasses import dataclass, field
from pathlib import Path

__all__ = [
    "DEFAULT_DATASET_ROOT",
    "RoundDataFrame",
    "Stabilizer",
    "WithinCycleStream",
    "XZZXSchedule",
    "default_r01_paths",
    "default_r10_paths",
    "extract_stabilizers",
    "parse_within_cycle_streams",
    "parse_xzzx_circuit",
]

# stim Pauli-byte (1/2/3) -> letter, sign-stripped.
_PAULI_BYTE = {1: "X", 2: "Y", 3: "Z"}


@dataclass(frozen=True)
class Stabilizer:
    """One compiled stabilizer parity-measurement op (the ``("stab", paulis, stab_id)``).

    ``paulis`` maps engine **data-register position** (``0..n_data-1``) -> ``'X'`` or
    ``'Z'`` (the XZZX support). ``stab_id`` is the stable index of this stabilizer in
    the parsed order (0..7 for d3). ``ancilla_index`` / ``coord`` carry the originating
    circuit ancilla qubit id + its (x, y) grid coordinate (provenance / audit).
    """

    stab_id: int
    paulis: dict[int, str]
    ancilla_index: int
    coord: tuple[float, ...]

    @property
    def kind(self) -> str:
        """'X' or 'Z' if the support is pure-X / pure-Z (always true for XZZX); else 'mixed'."""
        kinds = {str(p).upper() for p in self.paulis.values()}
        return next(iter(kinds)) if len(kinds) == 1 else "mixed"

    def as_op(self) -> tuple[str, dict[int, str], int]:
        """The contract Schedule op tuple ``("stab", paulis, stab_id)``."""
        return ("stab", dict(self.paulis), self.stab_id)


@dataclass(frozen=True)
class RoundDataFrame:
    """The per-round transversal single-qutrit DATA Pauli/Clifford FRAME of one QEC cycle.

    The supported external d3 XZZX circuit applies, on the DATA qubits, single-qutrit gates that are
    NOT part of the stabilizer-extraction basis rotation (those H rotations are compiled
    into the parity projection via ``Stabilizer.paulis`` / the engine's ``stab_supp_isx``).
    These FRAME gates are the mid-cycle transversal ``X`` echo and the post-measurement
    transversal ``Y`` (both ``|0><->|1>`` on the computational subspace, ``|2>`` inert):

      cycle:  ... CZ ... [X echo] ... CZ ... M(stab) ... [Y frame] ...

    They are a Pauli FRAME for the Clifford stabilizer/logical structure (the detectors and
    the observable are frame-invariant -- verified: removing them leaves every ideal-circuit
    detector deterministic), so they have **no effect on a Pauli/Clifford circuit's syndromes
    or logical outcome**. The within-cycle qutrit leakage channel is **non-Pauli**:
    The declared heating jump acts on ``|1>`` while ``|0>`` is leakage-inert. The ``X`` echo
    therefore changes the subsequent ``|1>``/``|2>`` leakage evolution and must be applied
    at its physical circuit position in the leakage trajectory.

    Attributes
    ----------
    pre_measure
        Ordered ``(gate_name, tuple[data_position])`` for the FRAME gates applied BEFORE the
        round's stabilizer measurement (the mid-cycle ``X`` echo for d3 XZZX), engine
        data-position order.
    post_measure
        Ordered ``(gate_name, tuple[data_position])`` for the FRAME gates applied AFTER the
        round's stabilizer measurement (the post-M ``Y`` for d3 XZZX; empty on the final
        round, which ends in the terminal data readout).

    ``gate_name`` is the stim single-qutrit gate (``X``/``Y``/``Z``/``S``/``S_DAG``); ``H`` is
    excluded as a basis rotation. ``data_position`` is the engine register position (the index
    into :attr:`XZZXSchedule.data_indices`), not the circuit qubit id.
    """

    pre_measure: tuple[tuple[str, tuple[int, ...]], ...]
    post_measure: tuple[tuple[str, tuple[int, ...]], ...]


#: Within-cycle stream tokens, refining ``RoundDataFrame`` at each data qutrit's physical
#: gate and leakage-channel insertion points. ``LEAK`` is a leak sub-step = ONE CZ-layer the qutrit touches
#: (where ``DEPOLARIZE2`` sits in the noisy circuit); the host applies ``exp(L/4)`` there.
#: ``H``/``X``/``Y`` are the literal single-qutrit gates (``|2>`` inert); ``M`` is the
#: stabilizer-measurement boundary (a marker, not a gate). The interior round 9-slot shape
#: is  ``[H?] LEAK [H?] LEAK X LEAK [H?] LEAK M Y``  (LEAKs present only for the CZ layers the
#: qutrit participates in — 2/3/4 of the 4 global layers).
_WITHIN_CYCLE_TOKENS: frozenset[str] = frozenset({"H", "X", "Y", "LEAK", "M"})


@dataclass(frozen=True)
class WithinCycleStream:
    """One data qutrit's ordered interior within-round gate-and-leak stream.

    The circuit-faithful per-cycle structure for a SINGLE data qutrit at engine register
    position :attr:`pos`: the ordered list of within-round steps
    (:attr:`tokens`), each one of ``H`` / ``X`` / ``Y`` (literal single-qutrit gate,
    ``|2>`` inert), ``LEAK`` (a leak sub-step at one CZ layer the qutrit touches — the host
    applies the ``exp(L/4)`` slice), or ``M`` (the stabilizer-measurement boundary marker).
    It is sourced from a multi-round circuit's interior rounds, not r01's single round,
    because r01 combines initialization and terminal-readout structure. Its per-qutrit
    H-slot distribution therefore differs from a clean interior round.

    Leakage-channel insertions are interleaved with the H/X gates at their circuit
    positions. The mid-cycle ``X`` echo lies between the qutrit's pre-X and post-X CZ
    layers, so the computational level entering each subsequent ``|1><->|2>`` exchange
    slice is represented explicitly rather than lumped into one per-round channel.

    The pre-M part (everything up to and including ``M``) is applied PER QUTRIT before the
    stabilizer measurement; the post-M ``Y`` is applied to all data AFTER it (dropped on the
    terminal round). Because single-qutrit ops on DISTINCT qutrits commute, each qutrit's
    stream is applied independently on the full state in its OWN internal order; the relative
    order ACROSS qutrits is immaterial.

    Attributes
    ----------
    pos
        Engine register position (index into :attr:`XZZXSchedule.data_indices`).
    circuit_id
        The circuit qubit id of this data qutrit in the SOURCE (interior-round) circuit
        (provenance; the engine keys everything by ``pos``).
    tokens
        The ordered within-round stream (``_WITHIN_CYCLE_TOKENS``), interior round.
    n_cz
        The number of ``LEAK`` sub-steps = CZ layers this qutrit participates in (2/3/4).
    cz_layers
        The 1-indexed CZ-layer ordinals (subset of ``{1,2,3,4}``) the qutrit touches.
    h_pattern
        ``(H@preCZ1, H@CZ1-2, H@CZ3-4)`` — the per-qutrit H presence at the three pre-M
        H-layer slots in the parsed XZZX schedule. Each qutrit has exactly 2 H's per
        interior round (even → net identity on ``{0,1}``).
    """

    pos: int
    circuit_id: int
    tokens: tuple[str, ...]
    n_cz: int
    cz_layers: tuple[int, ...]
    h_pattern: tuple[int, int, int]

    def pre_measure_tokens(self) -> tuple[str, ...]:
        """The ordered tokens up to (and EXCLUDING) the ``M`` boundary — the per-qutrit
        pre-measurement stream (H's + leaks + the mid-cycle X). Applied to the state before
        the stabilizer measurement."""
        out: list[str] = []
        for tok in self.tokens:
            if tok == "M":
                break
            out.append(tok)
        return tuple(out)

    def post_measure_tokens(self) -> tuple[str, ...]:
        """The ordered tokens AFTER the ``M`` boundary — the per-qutrit post-measurement
        frame (the transversal ``Y`` for an interior round; empty for the terminal round)."""
        seen_m = False
        out: list[str] = []
        for tok in self.tokens:
            if tok == "M":
                seen_m = True
                continue
            if seen_m:
                out.append(tok)
        return tuple(out)


@dataclass(frozen=True)
class XZZXSchedule:
    """The parsed d3 XZZX circuit, in the engine's data-register description.

    Attributes
    ----------
    n_data
        Number of data qutrits (9 for d3) = the engine ``QutritDM(n_data)`` register size.
    data_indices
        The circuit qubit ids of the data qutrits, in engine-position order
        (``data_indices[p]`` is the circuit id of engine position ``p``).
    data_coords
        The (x, y) grid coordinate of each engine data position (parallel to ``data_indices``).
    stabilizers
        The 8 :class:`Stabilizer` ops (X/Z supports on data positions), in parsed order.
    logical
        The protected observable as ``{data_position -> 'X'|'Z'}`` (``OBSERVABLE_INCLUDE``),
        ready for :meth:`QutritDM.set_code` (as ``logical_z`` for an X-basis Z observable).
    logical_kind
        'X' or 'Z' -- the Pauli type of the logical operator on the data.
    data_init_x
        The set of data positions the chosen sweep word initializes with an ``X`` gate
        (sweep-CX resolved); empty for the default all-zero sweep word.
    surplus_dropped
        Circuit qubit ids dropped as inert surplus (empty at r01; idx 0/7/19 at r10/r13).
    rounds
        The number of QEC rounds the source circuit declares (1 for r01).
    per_round_data_frame
        Per round (length == ``rounds``), the transversal single-qutrit DATA Pauli FRAME
        (:class:`RoundDataFrame`: the mid-cycle ``X`` echo + the post-M ``Y``) the circuit
        applies outside the stabilizer-extraction basis rotations. Empty per-round entries at r01
        (one round, no inter-round echo dynamics) are still recorded so the field is uniform.
    within_cycle_streams
        Per data qutrit (length ``n_data``, engine-position order), the ORDERED interior
        within-round gate+leak stream (:class:`WithinCycleStream`). Populated only for a multi-round source
        circuit (the interior round is well-defined there); EMPTY for r01 (a single
        first+terminal round, which is not a clean interior round). The
        host and dense reference both marshal the per-qutrit interleaving of
        leakage with H/X gates; ``per_round_data_frame`` is the coarser
        lumped-X/Y view.
    source
        The parsed ``circuit_ideal.stim`` path (provenance).
    """

    n_data: int
    data_indices: tuple[int, ...]
    data_coords: tuple[tuple[float, ...], ...]
    stabilizers: tuple[Stabilizer, ...]
    logical: dict[int, str]
    logical_kind: str
    data_init_x: frozenset[int]
    surplus_dropped: tuple[int, ...]
    rounds: int
    per_round_data_frame: tuple[RoundDataFrame, ...] = ()
    within_cycle_streams: tuple[WithinCycleStream, ...] = ()
    source: str = ""

    def stab_ops(self) -> list[tuple[str, dict[int, str], int]]:
        """The ordered list of contract ``("stab", paulis, stab_id)`` ops."""
        return [s.as_op() for s in self.stabilizers]

    def stab_paulis(self) -> list[dict[int, str]]:
        """The ordered list of stabilizer ``paulis`` dicts (the ``QutritDM`` ``stabs`` arg)."""
        return [dict(s.paulis) for s in self.stabilizers]

    def x_stabilizers(self) -> list[Stabilizer]:
        return [s for s in self.stabilizers if s.kind == "X"]

    def z_stabilizers(self) -> list[Stabilizer]:
        return [s for s in self.stabilizers if s.kind == "Z"]

    def pre_measure_data_gates(self) -> list[list[tuple[str, tuple[int, ...]]]]:
        """Per round, the ordered PRE-measurement transversal DATA frame gates (the ``X`` echo).

        ``out[r]`` is the list of ``(gate_name, data_positions)`` applied to the data qubits
        BEFORE round ``r``'s stabilizer measurement, outside the basis rotations. For d3 XZZX this is
        the single transversal ``X`` (all 9 data) per round. Empty list per round if the
        per-round frame was not parsed (e.g. r01); callers treat that as "no echo".
        """
        return [[(g, tuple(pos)) for g, pos in rf.pre_measure] for rf in self.per_round_data_frame]

    def within_cycle_by_pos(self) -> dict[int, WithinCycleStream]:
        """The within-cycle interior streams keyed by engine register position.

        ``{pos -> WithinCycleStream}`` for each data qutrit; empty dict if the source was a
        single-round circuit because no clean interior round exists at r01.
        Used by the host marshalling + the DM oracle to apply each qutrit's own interleaved
        ``[H?] LEAK [H?] LEAK X LEAK [H?] LEAK M Y`` stream.
        """
        return {s.pos: s for s in self.within_cycle_streams}

    def with_within_cycle_streams(
        self, streams: "tuple[WithinCycleStream, ...] | list[WithinCycleStream]"
    ) -> "XZZXSchedule":
        """Return a copy of this schedule with ``within_cycle_streams`` attached.

        The stabilizer geometry, logical observable, and codestate come from the
        extraction-validated r01 schedule, while the per-qutrit interior streams come from r10 via
        :func:`parse_within_cycle_streams`). This combiner attaches the r10 streams to an r01
        schedule. It asserts that the streams cover engine positions ``0..n_data-1`` exactly,
        so every r10 interior stream keys onto the same data coordinate used by r01.
        """
        from dataclasses import replace

        streams = tuple(streams)
        positions = sorted(s.pos for s in streams)
        if positions != list(range(self.n_data)):
            raise AssertionError(
                f"within-cycle streams cover positions {positions}, expected 0..{self.n_data - 1} "
                f"(the r10 interior streams must key onto the r01 schedule's {self.n_data} data "
                f"positions in the shared data-coordinate geometry)")
        return replace(self, within_cycle_streams=streams)


# --------------------------------------------------------------------------- #
# Low-level circuit reads (stim)                                              #
# --------------------------------------------------------------------------- #
def _index_to_coord(circuit) -> dict[int, tuple[float, ...]]:
    """``QUBIT_COORDS`` map: circuit qubit id -> (x, y, ...) coordinate."""
    import stim

    out: dict[int, tuple[float, ...]] = {}
    for inst in circuit.flattened():
        if isinstance(inst, stim.CircuitInstruction) and inst.name == "QUBIT_COORDS":
            args = tuple(float(a) for a in inst.gate_args_copy())
            for t in inst.targets_copy():
                if t.is_qubit_target:
                    out[int(t.qubit_value)] = args
    return out


def _classify_qubits(circuit, meta) -> tuple[list[int], list[int], list[int]]:
    """Partition the circuit qubit indices into (data, measure, surplus).

    data / measure are the indices whose coordinate matches a metadata
    ``data_qubit_coords`` / ``meas_qubit_coords`` entry (the abstract code); surplus
    = every declared index that is neither (the inert boundary slots are dropped).
    Each list is sorted by data-coordinate order for data (so positions are
    deterministic), by index for the rest.
    """
    idx2c = _index_to_coord(circuit)
    data_coords = [tuple(float(x) for x in c) for c in meta["data_qubit_coords"]]
    meas_coords = {tuple(float(x) for x in c) for c in meta["meas_qubit_coords"]}
    data_set = set(data_coords)

    # data positions follow the metadata data_qubit_coords ORDER (the engine register
    # convention): position p <-> data_qubit_coords[p].
    coord_to_index = {c: i for i, c in idx2c.items()}
    data_idx: list[int] = []
    for c in data_coords:
        if c not in coord_to_index:
            raise ValueError(f"data coord {c} from metadata not found in circuit QUBIT_COORDS")
        data_idx.append(coord_to_index[c])

    meas_idx = sorted(i for i, c in idx2c.items() if c in meas_coords)
    surplus_idx = sorted(i for i, c in idx2c.items() if c not in data_set and c not in meas_coords)
    return data_idx, meas_idx, surplus_idx


def _first_ancilla_measure_order(circuit) -> list[int]:
    """The qubit ids of the FIRST ``M`` instruction (the round's stabilizer readout).

    The round's data<->ancilla CZ chain ends with a single ``M`` over the 8 ancilla
    (their measurement order = the record order, used to align flow measurements). A
    later ``M`` over the data qubits is the final logical readout and is NOT this set.
    """
    import stim

    for inst in circuit.flattened():
        if isinstance(inst, stim.CircuitInstruction) and inst.name == "M":
            return [int(t.qubit_value) for t in inst.targets_copy() if t.is_qubit_target]
    raise ValueError("no M instruction found in circuit")


def _unitary_only_circuit(circuit):
    """The Clifford UNITARY prefix of the round (H / CZ / X), in order.

    Drops QUBIT_COORDS / sweep-CX / M / R / DETECTOR / OBSERVABLE_INCLUDE / TICK. The
    sweep-CX is the *ideal* all-zero-sweep data init = identity, so excluding it gives
    exactly the noiseless round unitary ``U`` whose Heisenberg action defines the
    stabilizers.
    """
    import stim

    u = stim.Circuit()
    for inst in circuit.flattened():
        if isinstance(inst, stim.CircuitInstruction) and inst.name in ("H", "CZ", "X", "Y", "S", "S_DAG"):
            u.append(inst)
    return u


# --------------------------------------------------------------------------- #
# Stabilizer extraction (Method 1: tableau pullback; Method 3b: cross-check)  #
# --------------------------------------------------------------------------- #
def _pullback_stabilizer(circuit, ancilla: int, data_idx: list[int]) -> dict[int, str]:
    """``U^dag Z_anc U`` restricted to data qutrits -> ``{circuit_data_id -> 'X'|'Z'}``.

    Heisenberg pullback through the round's Clifford ``U`` (the exact operator
    identity, Method 1). The ancilla's own ``Z_anc`` self-factor (it starts in |0>)
    is absorbed by the data-side projection and is excluded here; what remains on the
    data is the XZZX stabilizer support.
    """
    u = _unitary_only_circuit(circuit)
    tab = u.to_tableau(ignore_measurement=True, ignore_reset=True, ignore_noise=True)
    inv = tab.inverse()
    ps = inv.z_output(int(ancilla))  # = U^dag Z_anc U as a PauliString
    data_set = set(data_idx)
    out: dict[int, str] = {}
    for q in range(len(ps)):
        p = ps[q]
        if p != 0 and q in data_set:
            out[q] = _PAULI_BYTE[p]
    return out


def _error_response_supports(circuit, data_idx: list[int], anc_order: list[int]) -> dict[int, dict[str, set]]:
    """Deterministic single-Pauli-error -> ancilla-flip response (Method 3b).

    For each data qubit and each error type in {X, Z}, insert a 100% Pauli error right
    after the data init and XOR the 8 ancilla measurement outcomes against the
    error-free record under a FIXED seed (the X-ancilla raw outcomes are random
    shot-to-shot, but a commuting/anticommuting error flips an ancilla IDENTICALLY in
    every shot, so the same-seed XOR is deterministic). Returns
    ``{ancilla_id -> {'X': set(data flipping it via X-err), 'Z': set(... via Z-err)}}``
    -- a construction fully independent of the tableau pullback.
    """
    import stim

    def record8(err_q=None, etype=None, seed=777):
        out = stim.Circuit()
        inserted = False
        for inst in circuit.flattened():
            if isinstance(inst, stim.CircuitInstruction) and inst.name in ("DETECTOR", "OBSERVABLE_INCLUDE"):
                continue
            out.append(inst)
            if (isinstance(inst, stim.CircuitInstruction) and inst.name == "CX"
                    and not inserted and err_q is not None):
                out.append(etype + "_ERROR", [int(err_q)], 1.0)
                inserted = True
        sample = out.compile_sampler(seed=seed).sample(1)[0]
        return [bool(b) for b in sample[: len(anc_order)]]

    ref = record8()
    resp: dict[int, dict[str, set]] = {a: {"X": set(), "Z": set()} for a in anc_order}
    for q in data_idx:
        for et in ("X", "Z"):
            rec = record8(q, et)
            for i, a in enumerate(anc_order):
                if rec[i] != ref[i]:
                    resp[a][et].add(int(q))
    return resp


def extract_stabilizers(circuit, data_idx: list[int], anc_order: list[int], *, verify: bool = True):
    """Extract the XZZX stabilizer supports per ancilla, with a built-in cross-check.

    Returns ``{ancilla_id -> {circuit_data_id -> 'X'|'Z'}}`` in ``anc_order``. The
    primary extraction is the tableau pullback (Method 1, exact). When ``verify`` is
    set, the result is cross-checked against the deterministic error-response (Method
    3b): a Z-type stabilizer must be flipped by X-errors EXACTLY on its support and by
    no Z-error, and vice-versa for an X-type stabilizer. A disagreement raises
    ``AssertionError`` (the ``(a)``-class self-check -- a broken extraction fails
    loudly rather than emitting a wrong schedule).
    """
    pull = {a: _pullback_stabilizer(circuit, a, data_idx) for a in anc_order}

    if verify:
        resp = _error_response_supports(circuit, data_idx, anc_order)
        for a in anc_order:
            supp = pull[a]
            kinds = {v for v in supp.values()}
            if len(kinds) != 1:
                raise AssertionError(
                    f"ancilla {a}: pullback support is not pure-X/pure-Z (XZZX violated): {supp}"
                )
            kind = next(iter(kinds))
            sites = set(supp.keys())
            x_flips = resp[a]["X"]
            z_flips = resp[a]["Z"]
            if kind == "Z":
                # a Z-stabilizer detects X errors on its support (and no Z error)
                if x_flips != sites or z_flips:
                    raise AssertionError(
                        f"ancilla {a} Z-stab support {sorted(sites)} disagrees with error-response "
                        f"(X-flips={sorted(x_flips)}, Z-flips={sorted(z_flips)})"
                    )
            else:  # kind == 'X'
                if z_flips != sites or x_flips:
                    raise AssertionError(
                        f"ancilla {a} X-stab support {sorted(sites)} disagrees with error-response "
                        f"(Z-flips={sorted(z_flips)}, X-flips={sorted(x_flips)})"
                    )
    return pull


# --------------------------------------------------------------------------- #
# Logical observable + sweep-CX resolution                                    #
# --------------------------------------------------------------------------- #
def _logical_observable(circuit, data_idx: list[int]):
    """Extract ``OBSERVABLE_INCLUDE`` as ``{circuit_data_id -> 'X'|'Z'}`` (+ its kind).

    The observable references measurement records; for the final-readout ``M`` over the
    data qubits a ``rec`` resolves to a data qubit. The observable type (X or Z) is the
    one whose deterministic flow the circuit satisfies (``has_flow``): a Z observable in
    the X memory basis (the shipped ``d3_at_q6_7/X`` patch protects logical Z).
    """
    import stim

    # Map every measurement record index to the qubit it measures (in order).
    meas_qubits: list[int] = []
    for inst in circuit.flattened():
        if isinstance(inst, stim.CircuitInstruction) and inst.name == "M":
            meas_qubits.extend(int(t.qubit_value) for t in inst.targets_copy() if t.is_qubit_target)
    n_meas = len(meas_qubits)

    # The OBSERVABLE_INCLUDE targets (rec[-k]); resolve to data qubits.
    obs_data: list[int] = []
    obs_recs: list[int] = []
    for inst in circuit.flattened():
        if isinstance(inst, stim.CircuitInstruction) and inst.name == "OBSERVABLE_INCLUDE":
            for t in inst.targets_copy():
                if t.is_measurement_record_target:
                    rec = n_meas + int(t.value)  # t.value is negative (rec[-k])
                    obs_recs.append(rec)
                    q = meas_qubits[rec]
                    if q in set(data_idx):
                        obs_data.append(q)
    obs_data = sorted(set(obs_data))
    if not obs_data:
        raise ValueError("OBSERVABLE_INCLUDE resolved to no data qubits")

    # Determine the Pauli kind by deterministic flow verification (independent of any
    # assumption): a logical operator P on obs_data flows to the observable records.
    n = circuit.num_qubits
    kind = None
    for cand in ("Z", "X"):
        ps = ["_"] * n
        for q in obs_data:
            ps[q] = cand
        flow = stim.Flow(
            input=stim.PauliString("_" * n),
            output=stim.PauliString("".join(ps)),
            measurements=sorted(obs_recs),
        )
        try:
            ok = circuit.has_flow(flow)
        except Exception:
            ok = False
        if ok:
            kind = cand
            break
    if kind is None:
        # Fall back to the X-memory-basis convention (the patch is the X dir -> Z logical);
        # the engine reads parity regardless of kind, so this only labels the operator.
        kind = "Z"
    return {q: kind for q in obs_data}, kind


def _sweep_init_pattern(circuit, data_idx: list[int], sweep_word: dict[int, int] | None):
    """Resolve ``CX sweep[k] q`` to the set of data qubits initialized with X.

    ``CX sweep[k] q`` applies X to qubit ``q`` iff sweep bit ``k`` is 1 (dataset note
    (b)). ``sweep_word`` maps sweep-bit index -> 0/1; the default (``None``) is the
    all-zero word (the ideal noiseless circuit) -> NO data X-init. Returns the set of
    data qubit ids that get an X.
    """
    import stim

    sweep_word = sweep_word or {}
    x_data: set[int] = set()
    data_set = set(data_idx)
    for inst in circuit.flattened():
        if isinstance(inst, stim.CircuitInstruction) and inst.name == "CX":
            targets = inst.targets_copy()
            # targets alternate (sweep-bit, qubit)
            it = iter(targets)
            for sweep_t in it:
                q_t = next(it)
                if sweep_t.is_sweep_bit_target and q_t.is_qubit_target:
                    k = int(sweep_t.value)
                    q = int(q_t.qubit_value)
                    if sweep_word.get(k, 0) and q in data_set:
                        x_data.add(q)
    return x_data


# --------------------------------------------------------------------------- #
# Per-round transversal DATA Pauli frame (the X echo + Y frame)                #
# --------------------------------------------------------------------------- #
#: Single-qutrit DATA gates carried as a per-round FRAME (Pauli/Clifford that is NOT a
#: stabilizer-basis rotation). ``H`` is EXCLUDED -- it is the X-support Z-rotation the engine
#: performs inside the measurement (``stab_supp_isx``); ``I`` is a no-op. See
#: :class:`RoundDataFrame`. The d3 XZZX alphabet here is ``{X (mid-cycle echo), Y (post-M)}``;
#: ``Z``/``S``/``S_DAG`` are reserved so a circuit that adds them parses without a code change.
_FRAME_GATE_NAMES: frozenset[str] = frozenset({"X", "Y", "Z", "S", "S_DAG"})


def _per_round_data_frame(
    circuit, data_idx: list[int], meas_idx: list[int]
) -> list["RoundDataFrame"]:
    """Extract, per QEC round, the transversal single-qutrit DATA Pauli FRAME (:class:`RoundDataFrame`).

    The instruction stream is segmented into rounds at each STABILIZER measurement (the ``M``
    over the 8 measure qubits with no data target); within a round the FRAME gates
    (``_FRAME_GATE_NAMES``, i.e. ``X``/``Y``/``Z``/``S``/``S_DAG`` -- ``H`` excluded as a basis
    rotation) on data qubits are recorded in circuit order, tagged BEFORE (``pre_measure``) vs
    AFTER (``post_measure``) that round's stabilizer ``M``. Data qubit ids are remapped to
    engine register positions (the index into ``data_idx``). Returns one entry per round (the
    final round's ``post_measure`` is empty -- it ends in the terminal data readout, not a
    post-M frame).

    Rigorous, not pattern-matched: it keys off the literal stim gate names + the data/measure
    partition (the same partition the stabilizer extraction uses). For d3 XZZX every interior
    round yields exactly the transversal ``X`` (all data, pre-M) + the post-M ``Y`` -- verified
    across all supported external d3 patches/bases.
    """
    import stim

    data_set, meas_set = set(data_idx), set(meas_idx)
    pos_of = {cid: p for p, cid in enumerate(data_idx)}
    insts = [i for i in circuit.flattened() if isinstance(i, stim.CircuitInstruction)]

    rounds: list[RoundDataFrame] = []
    cur_pre: list[tuple[str, tuple[int, ...]]] = []
    cur_post: list[tuple[str, tuple[int, ...]]] = []
    phase = "pre"  # 'pre' = before this round's stab-M; 'post' = the post-M frame
    for inst in insts:
        nm = inst.name
        if nm == "M":
            qs = [int(t.qubit_value) for t in inst.targets_copy() if t.is_qubit_target]
            is_stab_M = bool(set(qs) & meas_set) and not (set(qs) & data_set)
            if is_stab_M:
                phase = "post"
            # the terminal data ``M`` is not a round boundary (it ends the circuit body)
            continue
        if nm == "CZ" and phase == "post":
            # a CZ after the stab-M opens the NEXT round's extraction network -> close this round
            rounds.append(RoundDataFrame(pre_measure=tuple(cur_pre), post_measure=tuple(cur_post)))
            cur_pre, cur_post = [], []
            phase = "pre"
            continue
        if nm in _FRAME_GATE_NAMES:
            qs = [int(t.qubit_value) for t in inst.targets_copy() if t.is_qubit_target]
            dpos = tuple(sorted(pos_of[q] for q in qs if q in data_set))
            if dpos:
                (cur_post if phase == "post" else cur_pre).append((nm, dpos))
    rounds.append(RoundDataFrame(pre_measure=tuple(cur_pre), post_measure=tuple(cur_post)))
    return rounds


# --------------------------------------------------------------------------- #
# Per-qutrit within-cycle interior gate-and-leak stream                          #
# --------------------------------------------------------------------------- #
def _tick_layers(circuit) -> list[list]:
    """Segment the flattened instruction stream into TICK-delimited LAYERS.

    ``out[k]`` is the list of stim ``CircuitInstruction``s between TICK ``k-1`` and ``k``
    (TICKs themselves dropped; empty layers dropped). The qutrit gates of one round's CZ
    network sit in distinct TICK-layers, so layer indices order the within-round stream.
    """
    import stim

    flat: list[list] = [[]]
    for inst in circuit.flattened():
        if not isinstance(inst, stim.CircuitInstruction):
            continue
        if inst.name == "TICK":
            flat.append([])
            continue
        flat[-1].append(inst)
    return [ly for ly in flat if ly]


def _interior_round_layers(circuit, data_set: set[int], anc_set: set[int]) -> list[list]:
    """The TICK-layers of ONE clean INTERIOR round (round index 1) of a multi-round circuit.

    Round boundaries open at a reset ``R`` layer; round index 1 is the SECOND round — the
    first round (index 0) folds the extra data-init H layer (the logical-state prep) and the
    LAST round drops the post-M Y (terminal readout), so neither is a clean interior round.
    Round 1 supplies the interior gate/leak ordering reused for R>1.
    Returns ``[]`` if the circuit has fewer than 2 reset-delimited rounds (e.g. r01).
    """
    layers = _tick_layers(circuit)
    round_of: list[int] = []
    cur = -1
    for ly in layers:
        if any(i.name == "R" for i in ly):
            cur += 1
        round_of.append(cur)
    if cur < 1:  # <2 rounds -> no clean interior round (single-round r01)
        return []
    return [ly for li, ly in enumerate(layers) if round_of[li] == 1]


def _within_cycle_streams(
    circuit, data_idx: list[int], meas_idx: list[int]
) -> list[WithinCycleStream]:
    """Extract each data qutrit's ordered interior within-round gate-and-leak stream.

    For one clean INTERIOR round (:func:`_interior_round_layers`), emit per data qutrit (by
    engine register position = index into ``data_idx``) the ordered token stream
    ``[H?] LEAK [H?] LEAK X LEAK [H?] LEAK M Y``, where each ``LEAK`` is one CZ layer the
    qutrit participates in (a leak sub-step), ``H``/``X``/``Y`` are its literal single-qutrit
    gates, and ``M`` is the stabilizer-measurement boundary. This one-site stream does not
    encode the two-site CZ leakage-transport operation itself; it retains the corresponding
    leakage-channel insertion point (where ``DEPOLARIZE2`` sits in the noisy circuit), and
    the host applies the ``exp(L/4)`` slice at every ``LEAK``.

    Rigorous, not pattern-matched: it walks the literal stim gate names per TICK-layer and
    keys off the data/measure partition (the same partition the stabilizer extraction uses).
    Returns ``[]`` for a single-round circuit because it has no clean interior round;
    source the interior stream from a multi-round circuit. The 4-CZ global layer count, the
    mid-cycle X between CZ-layer 2 and 3, the per-qutrit 2-H even count, and the 4 distinct
    H-patterns are asserted as structural checks on the extracted physical schedule.
    """
    data_set, meas_set = set(data_idx), set(meas_idx)
    pos_of = {cid: p for p, cid in enumerate(data_idx)}
    layers = _interior_round_layers(circuit, data_set, meas_set)
    if not layers:
        return []

    # The CZ-layer ordinals (1-indexed) at which any data qutrit leaks, in circuit order.
    cz_layer_indices = [li for li, ly in enumerate(layers) if any(i.name == "CZ" for i in ly)]
    if len(cz_layer_indices) != 4:
        raise AssertionError(
            f"within-cycle: expected 4 CZ layers per interior round, got {len(cz_layer_indices)} "
            f"(the four physical leak-substep insertion layers)")

    # Per qutrit, walk the layers in order, emitting tokens. A CZ-layer the qutrit touches
    # -> 'LEAK'; an H/X/Y on it -> the gate; the stabilizer M -> 'M' (once, for all data).
    streams_tok: dict[int, list[str]] = {p: [] for p in range(len(data_idx))}
    cz_layers_of: dict[int, list[int]] = {p: [] for p in range(len(data_idx))}
    cz_ordinal = {li: k + 1 for k, li in enumerate(cz_layer_indices)}  # layer-idx -> 1..4
    for li, layer in enumerate(layers):
        for inst in layer:
            nm = inst.name
            if nm in ("H", "X", "Y"):
                for t in inst.targets_copy():
                    if t.is_qubit_target and int(t.qubit_value) in data_set:
                        streams_tok[pos_of[int(t.qubit_value)]].append(nm)
            elif nm == "CZ":
                ts = [int(t.qubit_value) for t in inst.targets_copy() if t.is_qubit_target]
                for a, b in zip(ts[0::2], ts[1::2]):
                    if a in data_set:
                        streams_tok[pos_of[a]].append("LEAK")
                        cz_layers_of[pos_of[a]].append(cz_ordinal[li])
                    if b in data_set:
                        streams_tok[pos_of[b]].append("LEAK")
                        cz_layers_of[pos_of[b]].append(cz_ordinal[li])
            elif nm == "M":
                qs = {int(t.qubit_value) for t in inst.targets_copy() if t.is_qubit_target}
                if qs and not (qs & data_set) and (qs & meas_set):  # stabilizer M (ancilla only)
                    for p in range(len(data_idx)):
                        streams_tok[p].append("M")

    # The global mid-cycle X layer and the 1-indexed CZ ordinals before/after it determine
    # the per-qutrit H-slot pattern.
    x_layers = [li for li, ly in enumerate(layers)
                if any(i.name == "X" and {int(t.qubit_value) for t in i.targets_copy()
                                          if t.is_qubit_target} & data_set for i in ly)]
    if len(x_layers) != 1:
        raise AssertionError(f"within-cycle: expected one mid-cycle X layer, got {len(x_layers)}")
    x_layer = x_layers[0]
    cz_before_x = [cz_ordinal[li] for li in cz_layer_indices if li < x_layer]
    cz_after_x = [cz_ordinal[li] for li in cz_layer_indices if li > x_layer]
    if cz_before_x != [1, 2] or cz_after_x != [3, 4]:
        raise AssertionError(
            f"within-cycle: mid-cycle X is not between CZ-layer 2 and 3 "
            f"(before={cz_before_x}, after={cz_after_x})")

    streams: list[WithinCycleStream] = []
    for p in range(len(data_idx)):
        toks = tuple(streams_tok[p])
        czs = tuple(cz_layers_of[p])
        n_cz = len(czs)
        # the three pre-M H-layer slots: preCZ1 (before any LEAK), CZ1-CZ2 (between the 1st
        # and 2nd LEAK), CZ3-CZ4 (between the 3rd and 4th LEAK in CZ-ordinal terms). We derive
        # the H presence by which CZ-ordinal gaps the H's fall in, robust to the per-qutrit nCZ.
        h_pat = _within_cycle_h_pattern(toks, czs)
        if (n_cz < 2 or n_cz > 4):
            raise AssertionError(f"within-cycle pos {p}: nCZ={n_cz} outside the expected 2..4")
        if toks.count("H") != 2:
            raise AssertionError(
                f"within-cycle pos {p}: {toks.count('H')} H's (expected exactly 2 per interior "
                f"round → even, net identity on {{0,1}}); stream {toks}")
        streams.append(WithinCycleStream(
            pos=p, circuit_id=int(data_idx[p]), tokens=toks, n_cz=n_cz,
            cz_layers=czs, h_pattern=h_pat,
        ))

    # Structural cross-check: the nine data qutrits have four distinct H-slot patterns.
    patterns = {s.h_pattern for s in streams}
    if len(streams) == 9 and len(patterns) != 4:
        raise AssertionError(
            f"within-cycle: expected 4 distinct H-patterns across the 9 data qutrits "
            f"got {len(patterns)}: {sorted(patterns)}")
    return streams


def _within_cycle_h_pattern(tokens: tuple[str, ...], cz_layers: tuple[int, ...]) -> tuple[int, int, int]:
    """Return ``(H@preCZ1, H@CZ1-2, H@CZ3-4)`` for one interior stream.

    An ``H`` is assigned to a slot by how many of the qutrit's own
    ``LEAK`` (CZ) tokens precede it in the stream (NOT the global CZ-layer ordinal) —
    ``0`` preceding ⇒ pre-CZ1, ``1`` ⇒ the CZ1-2 slot, ``2`` ⇒ the (unreported) CZ2-3 gap,
    ``3`` ⇒ the CZ3-4 slot. The three reported slots are
    (H@preCZ1, H@CZ1-2, H@CZ3-4); an H with 2 preceding leaks (e.g. q1's post-X H, which sits
    after its 2 leaks but before the global CZ3) falls in the CZ2-3 gap and is correctly NOT
    counted in any of the three (so q1 = (0,1,0), not (0,1,1)). ``cz_layers`` is accepted for
    signature symmetry but the count is determined by stream position.
    """
    h_pre = h_12 = h_34 = 0
    n_leak_before = 0  # the qutrit's OWN leak (CZ) tokens seen so far
    for tok in tokens:
        if tok == "M":
            break
        if tok == "LEAK":
            n_leak_before += 1
            continue
        if tok == "X":
            continue  # the X is not a CZ; it does not advance the leak count
        if tok == "H":
            if n_leak_before == 0:
                h_pre += 1            # before the qutrit's 1st leak (pre-CZ1 slot)
            elif n_leak_before == 1:
                h_12 += 1             # between the qutrit's 1st and 2nd leak (CZ1-2 slot)
            elif n_leak_before == 3:
                h_34 += 1             # between the qutrit's 3rd and 4th leak (CZ3-4 slot)
            # n_leak_before == 2 (the CZ2-3 gap) or >=4 (post-CZ4) is NOT a reported slot.
    return (h_pre, h_12, h_34)


# --------------------------------------------------------------------------- #
# Top-level parse                                                             #
# --------------------------------------------------------------------------- #
def parse_xzzx_circuit(
    circuit_path: str | Path,
    metadata_path: str | Path | None = None,
    *,
    sweep_word: dict[int, int] | None = None,
    verify: bool = True,
) -> XZZXSchedule:
    """Parse an external d3 XZZX ``circuit_ideal.stim`` into an :class:`XZZXSchedule`.

    Parameters
    ----------
    circuit_path
        Path to ``circuit_ideal.stim`` (use the **r01** instance for the R=1 floor --
        natively 17 qubits / 8 detectors, no surplus).
    metadata_path
        Path to the sibling ``metadata.json`` (default: ``circuit_path``'s directory).
        Used to classify data vs measure qubits (the abstract code coordinates).
    sweep_word
        Optional ``{sweep_bit_index -> 0/1}`` data-init word (default all-zero = the
        ideal noiseless circuit -> no data X-init).
    verify
        Run the built-in two-method stabilizer cross-check (default True).

    Returns
    -------
    XZZXSchedule
        The data-register description: 9 data positions, 8 ``("stab", paulis, stab_id)``
        ops on data positions, the logical observable, the resolved data-init pattern,
        the dropped surplus, the round count.
    """
    import json

    import stim

    circuit_path = Path(circuit_path)
    if metadata_path is None:
        metadata_path = circuit_path.parent / "metadata.json"
    metadata_path = Path(metadata_path)

    circuit = stim.Circuit.from_file(str(circuit_path))
    meta = json.loads(Path(metadata_path).read_text())

    data_idx, meas_idx, surplus_idx = _classify_qubits(circuit, meta)
    n_data = len(data_idx)
    if n_data != len(meta["data_qubit_coords"]):
        raise ValueError(f"data-qubit count mismatch: parsed {n_data} vs meta {len(meta['data_qubit_coords'])}")

    idx2c = _index_to_coord(circuit)
    data_coords = tuple(idx2c[i] for i in data_idx)

    # circuit-id -> engine data position (0..n_data-1), in metadata data-coord order.
    pos_of = {cid: p for p, cid in enumerate(data_idx)}

    anc_order = _first_ancilla_measure_order(circuit)
    # keep only ancilla that are actual measure qubits (drop any surplus that sneaks in)
    anc_order = [a for a in anc_order if a in set(meas_idx)]

    raw_stabs = extract_stabilizers(circuit, data_idx, anc_order, verify=verify)

    stabilizers: list[Stabilizer] = []
    for sid, a in enumerate(anc_order):
        supp_circuit = raw_stabs[a]
        # remap circuit data ids -> engine data positions
        paulis = {pos_of[cid]: kind for cid, kind in supp_circuit.items()}
        stabilizers.append(
            Stabilizer(stab_id=sid, paulis=paulis, ancilla_index=int(a), coord=idx2c[a])
        )

    logical_circuit, logical_kind = _logical_observable(circuit, data_idx)
    logical = {pos_of[cid]: kind for cid, kind in logical_circuit.items()}

    x_data_circuit = _sweep_init_pattern(circuit, data_idx, sweep_word)
    data_init_x = frozenset(pos_of[cid] for cid in x_data_circuit)

    rounds = int(meta.get("rounds", 1))

    # Per-round transversal DATA Pauli frame (the mid-cycle X echo + post-M Y), which changes
    # the level entering later non-Pauli leakage slices. Parsed from the circuit's intra-round
    # structure; the count is reconciled against ``rounds``.
    per_round_frame = tuple(_per_round_data_frame(circuit, data_idx, meas_idx))
    if per_round_frame and len(per_round_frame) != rounds:
        raise AssertionError(
            f"per-round data-frame count {len(per_round_frame)} != declared rounds {rounds} "
            f"(circuit {circuit_path}); the round segmentation disagrees with metadata")

    # Per-qutrit within-cycle interior gate-and-leak streams.
    # Defined only for a multi-round source circuit (a clean interior round exists); empty for
    # r01, whose single round combines first-round and terminal structure. The interior geometry is the
    # one the engine reuses for R>1; the host + DM oracle marshal each qutrit's interleaved
    # H/X/leak stream from this. (CZ-leak geometry is reuse-stable r01<->r10, but the per-qutrit
    # H-slot distribution is interior-round-specific, so this is sourced ONLY from the
    # multi-round circuit, never r01.)
    within_cycle = tuple(_within_cycle_streams(circuit, data_idx, meas_idx))

    return XZZXSchedule(
        n_data=n_data,
        data_indices=tuple(data_idx),
        data_coords=data_coords,
        stabilizers=tuple(stabilizers),
        logical=logical,
        logical_kind=logical_kind,
        data_init_x=data_init_x,
        surplus_dropped=tuple(surplus_idx),
        rounds=rounds,
        per_round_data_frame=per_round_frame,
        within_cycle_streams=within_cycle,
        source=str(circuit_path),
    )


def parse_within_cycle_streams(
    circuit_path: str | Path, metadata_path: str | Path | None = None
) -> tuple[WithinCycleStream, ...]:
    """Extract the per-qutrit interior streams from a multi-round circuit.

    The stabilizer-geometry-free companion to :func:`parse_xzzx_circuit` for the within-cycle
    leakage trajectory: it needs only the data/measure partition (from the metadata code coordinates) and the
    interior-round gate/CZ/M structure — NOT the stabilizer pullback (which is validated on r01,
    not r10). So a multi-round instance (r10) whose surplus/reset structure the full
    stabilizer extraction does not normalize can still yield its interior streams here.

    Use this to source the per-qutrit interior streams from a multi-round circuit (r10) while the
    stabilizers / logical / codestate come from the r01 schedule's reuse-stable geometry.
    Returns the streams keyed by engine register position (the metadata
    ``data_qubit_coords`` order; the SAME positions :func:`parse_xzzx_circuit` assigns), or ``()``
    for a single-round circuit (no clean interior round).
    """
    import json

    import stim

    circuit_path = Path(circuit_path)
    if metadata_path is None:
        metadata_path = circuit_path.parent / "metadata.json"
    metadata_path = Path(metadata_path)
    circuit = stim.Circuit.from_file(str(circuit_path))
    meta = json.loads(metadata_path.read_text())
    data_idx, meas_idx, _surplus = _classify_qubits(circuit, meta)
    return tuple(_within_cycle_streams(circuit, data_idx, meas_idx))


# --------------------------------------------------------------------------- #
# Convenience: locate an external d3_at_q6_7 patch in the portable data root  #
# --------------------------------------------------------------------------- #
def _default_dataset_root() -> Path:
    """Return the portable user-data location for the external Google dataset."""
    configured = os.environ.get("XDG_DATA_HOME", "").strip()
    data_home = Path(configured).expanduser() if configured else Path.home() / ".local" / "share"
    return data_home / "error-coupling-simulator" / "google_105Q_surface_code_d3_d5_d7"


DEFAULT_DATASET_ROOT = _default_dataset_root()


def default_r01_paths(
    patch: str = "d3_at_q6_7",
    basis: str = "X",
    *,
    dataset_root: str | Path | None = None,
) -> tuple[Path, Path]:
    """The (circuit_ideal.stim, metadata.json) paths for an external r01 d3 patch.

    r01 is the R=1 deliverable instance: natively 17 qubits / 8 detectors, no surplus.
    """
    root = DEFAULT_DATASET_ROOT if dataset_root is None else Path(dataset_root)
    base = root / patch / basis / "r01"
    return base / "circuit_ideal.stim", base / "metadata.json"


def default_r10_paths(
    patch: str = "d3_at_q6_7",
    basis: str = "X",
    *,
    dataset_root: str | Path | None = None,
) -> tuple[Path, Path]:
    """The (circuit_ideal.stim, metadata.json) paths for an external r10 d3 patch.

    r10 supplies the multi-round interior gate/leak ordering used for R>1; r01's single
    round combines first-round and terminal structure and is not a clean interior round.
    Use r10 to populate :attr:`XZZXSchedule.within_cycle_streams`.
    """
    root = DEFAULT_DATASET_ROOT if dataset_root is None else Path(dataset_root)
    base = root / patch / basis / "r10"
    return base / "circuit_ideal.stim", base / "metadata.json"
