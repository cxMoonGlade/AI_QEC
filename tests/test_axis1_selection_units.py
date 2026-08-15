"""Per-unit L0+L1+L2 coverage of
``error_coupling_simulator.frontend.axis1_selection`` (15 CPU-pure public units: the three
frozen Axis-1 selection dataclasses -- ``Axis1MechanismSelection`` (__post_init__ +
to_manifest), ``Axis1MechanismSelectionPlan`` (__post_init__ + by_kind + require_kind +
to_manifest), ``Axis1SelectionLayer`` (__post_init__ + participants + selection_ids +
to_manifest) -- and the five module functions ``axis1_selection_layers_in_schedule_order`` /
``flatten_axis1_selection_layers`` / ``axis1_selection_partition_manifest`` /
``build_axis1_joint_channel_selection_plan`` / ``build_axis1_schedule_selection_plan``; no torch, no
quimb, so out_of_scope is empty).

The module imports NEITHER torch NOR quimb (dataclasses + sibling frontend imports), so every
public unit is CPU-PURE and IN-SCOPE for full L0+L1+L2. The AST reconcile refuses any
gpu_bound claim; out_of_scope is {}.

L2 DISCIPLINE (100% coverage != discrimination). The two ``build_*`` selectors dispatch over a
large private-helper bank (``_cz_exact_zero_selections`` / ``_generic_*_selections`` /
``_drive_zz_selections`` / ...) that hard-codes each row's ``row_kind`` / ``primitive_names`` /
``mechanism_pair`` / ``context_mechanisms`` / ``reason`` / ``coupling_edges``. These helpers are
NOT reconciled units but ARE mutation-covered through the two public build entry points; so the
core discrimination is a per-row_kind BATTERY that compiles a curated circuit and pins the
resulting selection's exact fields (kills the row_kind/primitive/mechanism/reason string
mutants and the branch that chose the row) plus exact ``to_manifest`` dicts on representative
operation shapes (H / I-with-arg / M-with-basis-keys / CZ / coupling-edge-present).

RAISING-GUARD ROUTE COVERAGE + REACHABILITY PROBES. Every validation raise
in ``Axis1MechanismSelection.__post_init__`` is tripped by DIRECT construction with the exact
message; the ``axis1_selection_layers_in_schedule_order`` guards are tripped through BOTH the
build_* path (partition of a real plan) and a hand-built-selection path, with the EXACT message
via ``str(excinfo.value)==...`` -- and, because the message embeds ``consumer_name``, with a
non-default ``consumer_name`` too. The empty-participant guard is reachable only by forcing an
already-constructed selection's ``participant`` to ``()`` (the dataclass __post_init__ forbids it
at construction) -- an ``object.__setattr__`` probe, mirroring the analog_schedule seal probe.

DEAD-DEFENSIVE branches, probed not assumed (see the two ``line`` exemptions in the registry):
``Axis1MechanismSelection.__post_init__`` normalizes every coupling edge through ``_normal_pair``
(which returns a distinct 2-tuple or raises) BEFORE the second edge loop, so that loop's
``if len(edge) != 2 or edge[0] == edge[1]:`` re-check can never fire; and a coupling edge that
survives the containment check forces >= 2 distinct participants, so the zz-cluster
``if len(participant) < 2:`` guard can never fire either. Both are proven dead by the tests that
drive every REACHABLE edge/participant route.
"""
from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from _support.faithfulness import assert_discriminates, assert_pins, assert_raises_exact
from _support.fixtures import canonical_sealed_schedule

from error_coupling_simulator.frontend.axis1_selection import (
    AXIS1_JOINT_CHANNEL_SELECTOR_ID,
    AXIS1_SCHEDULE_SELECTOR_ID,
    AXIS1_SELECTION_SCHEMA,
    AXIS1_SELECTION_PARTITION_SCHEMA,
    AXIS1_SUPPORTED_SELECTION_ROW_KINDS,
    Axis1MechanismSelection,
    Axis1MechanismSelectionPlan,
    Axis1SelectionLayer,
    axis1_selection_layers_in_schedule_order,
    axis1_selection_partition_manifest,
    build_axis1_joint_channel_selection_plan,
    build_axis1_schedule_selection_plan,
    flatten_axis1_selection_layers,
)
from error_coupling_simulator.frontend.circuit_ir import CircuitBuilder
from error_coupling_simulator.frontend.analog_schedule import (
    circuit_ir_to_substep_schedule,
)
from error_coupling_simulator.frontend.axis1_context import (
    Axis1LocalLindbladContextSpec,
)


# --------------------------------------------------------------------------- #
# helpers                                                                       #
# --------------------------------------------------------------------------- #
def _raises_exact(exc, msg, fn):
    """pytest.raises pinning the EXACT ``str(exc)`` (kills string-literal wrap/case mutants a
    substring ``match=`` would let survive)."""
    with pytest.raises(exc) as ei:
        fn()
    assert str(ei.value) == msg, f"message mismatch\n got: {str(ei.value)!r}\n exp: {msg!r}"


def _sched(builder: CircuitBuilder):
    """Compile a CircuitBuilder to a sealed SubstepSchedule (the CPU-pure compiler path)."""
    return circuit_ir_to_substep_schedule(builder.build())


def _schedule_plan(builder: CircuitBuilder) -> Axis1MechanismSelectionPlan:
    return build_axis1_schedule_selection_plan(_sched(builder))


def _joint_channel_plan(builder: CircuitBuilder) -> Axis1MechanismSelectionPlan:
    return build_axis1_joint_channel_selection_plan(_sched(builder))


def _fields(sel: Axis1MechanismSelection) -> tuple:
    """The load-bearing, helper-chosen fields of ONE selection (independent of the substep
    passthrough) -- pinning these kills the row_kind/primitive/mechanism/context/reason/edge
    string+tuple mutants and the branch that selected the row."""
    return (
        sel.selection_id,
        sel.row_kind,
        sel.participant,
        sel.primitive_names,
        sel.mechanism_pair,
        sel.context_mechanisms,
        sel.coupling_edges,
        sel.reason,
    )


def _mk_sel(**over) -> Axis1MechanismSelection:
    """A minimal VALID Axis1MechanismSelection; override any field to trip a guard."""
    base = dict(
        selection_id="sel", row_kind="idle_cluster_joint_channel", substep_id="s0000",
        substep_kind="idle", participant=(0,), primitive_names=("T2", "T1"),
        mechanism_pair=("IDLE", "T2_T1_CLUSTER"), context_mechanisms=("T2", "T1"),
        operation_names=("I",), source_step_indices=(0,),
        operation_records=({"name": "I", "targets": [0]},), dt_ns_nominal=50.0,
        dt_ns_bracket=(50.0, 50.0), dt_source="explicit_circuit_idle_duration",
        mechanism_slots=("idle",), reason="r", coupling_edges=(),
    )
    base.update(over)
    return Axis1MechanismSelection(**base)


# --------------------------------------------------------------------------- #
# exact reasons (golden literals -- a mutation of any reason string in the src  #
# helper flips the pinned value -> killed)                                      #
# --------------------------------------------------------------------------- #
R_1Q_LOCAL = ("supported active-only one-qubit frontend control; generic joint-channel "
              "evidence embeds the ideal control term plus local T1/T2 context")
R_1Q_JOINT = ("supported one-qubit frontend control with an idle reference spectator; generic "
              "joint-channel evidence adds the ideal control term plus both-qubit Markovian "
              "context but no static-ZZ primitive")
R_1Q_CLUSTER = ("supported one-qubit frontend control with multiple idle spectators and no "
                "declared static-ZZ spectator; generic joint-channel evidence embeds the ideal "
                "control and all local T1/T2 spectator context in one union-support generator")
R_MULTI_1Q_LOCAL = ("supported active-only multi-one-qubit frontend-control layer; generic "
                    "joint-channel evidence embeds all ideal one-qubit controls and local T1/T2 "
                    "context in one active-support generator")
R_MULTI_1Q_CLUSTER = ("supported multi-active one-qubit frontend-control layer with visible idle "
                      "spectators and no declared static-ZZ edge inside the visible support; "
                      "generic joint-channel evidence embeds all ideal one-qubit controls and all "
                      "local T1/T2 context in one union-support generator")
R_1Q_ZZ_JOINT = ("supported one-qubit frontend control with a single idle spectator on a declared "
                 "static-ZZ pair; generic joint-channel evidence adds the ideal control term plus "
                 "both-qubit Markovian context")
R_1Q_ZZ_CLUSTER = ("supported one-qubit frontend-control substep with declared static-ZZ edge(s) "
                   "inside the visible active+idle support; generic joint-channel evidence embeds "
                   "all ideal one-qubit controls, all declared static-ZZ Hamiltonian edges in the "
                   "support, and all local T1/T2 context in one union-support generator")
R_IDLE_CLUSTER = ("explicit-duration idle substep over one or more idle qubits; generic "
                  "joint-channel evidence embeds local T1/T2 idle context in one union-support "
                  "generator")
R_IDLE_PAIR = ("explicit-duration idle pair; generic joint-channel evidence includes both-qubit "
               "Markovian idle context")
R_IDLE_ZZ_CLUSTER = ("explicit-duration idle substep with declared static-ZZ edge(s) inside the "
                     "idle support; generic joint-channel evidence embeds all declared static-ZZ "
                     "Hamiltonian edges and local T1/T2 idle context in one union-support "
                     "generator")
R_2Q_ZZ_BASE = ("CZ participant selects a same-substep CZ/ZZ carrier window; generic "
                "joint-channel evidence adds the ideal CZ control term plus both-qubit Markovian "
                "context")
R_2Q_ZZ_NOEDGE = R_2Q_ZZ_BASE + " without declaring persistent static-ZZ metadata"
R_2Q_ZZ_EDGE = R_2Q_ZZ_BASE + ("; public static-ZZ metadata declares the active pair and is "
                               "recorded as provenance for the same local ZZ carrier without "
                               "adding a second ZZ term")
R_2Q_CTRL_JOINT_CX = ("CX participant declares an ordered frontend-control window; generic "
                      "joint-channel evidence adds the ideal CX control term plus both-qubit "
                      "Markovian context")
R_2Q_CLUSTER = ("supported two-qubit frontend-control substep with visible idle spectators and no "
                "declared static-ZZ edge inside the visible support; generic joint-channel "
                "evidence embeds all ideal two-qubit controls and all local T1/T2 context in one "
                "union-support generator")
R_2Q_ZZ_CLUSTER = ("supported two-qubit frontend-control substep with visible idle spectators or "
                   "cross-window declared static-ZZ edge(s) inside the active+idle support; "
                   "generic joint-channel evidence embeds all ideal two-qubit controls, all "
                   "declared static-ZZ Hamiltonian edges in the support, and all local T1/T2 "
                   "context in one union-support generator")
R_RD_CLUSTER = ("explicit-duration Z readout window over one or more measured qubits; generic "
                "joint-channel evidence embeds readout dephasing on measured qubits and local "
                "T1/T2 context in one union-support generator before projective measurement "
                "branching")
R_RD_PAIR = ("explicit-duration Z readout pair; generic joint-channel evidence applies "
             "readout-window dephasing plus both-qubit Markovian context before projective "
             "measurement branching")
R_RD_ZZ_CLUSTER = ("explicit-duration Z readout window with declared static-ZZ edge(s) inside the "
                   "measured+idle support; generic joint-channel evidence embeds readout dephasing "
                   "on measured qubits, declared static-ZZ Hamiltonian edges, and local T1/T2 "
                   "context in one union-support generator before projective measurement "
                   "branching")
R_ZZ_T2_EXACT = ("explicit CZ participant supplies the registered same-substep ZZ x T2 exact-zero "
                 "diagnostic row; persistent static-ZZ couplings are not inferred from CZ history")
R_DR_ZZ = ("drive gate on one qubit with idle spectator on a declared static-ZZ pair; context "
           "includes T2/T1")


# =========================================================================== #
# build_axis1_schedule_selection_plan -- the per-row_kind BATTERY               #
# each entry pins the EXACT helper-chosen fields of every selection produced.   #
# =========================================================================== #
def _b(n, *, zz=None):
    b = CircuitBuilder(n)
    if zz is not None:
        b.declare_static_zz_couplings(zz)
    return b


# (case_id, builder-thunk, [ (fields-tuple), ... ])
_BATTERY = [
    ("one_qubit_drive_local",
     lambda: _b(1).h(0),
     [("s0000:one_qubit_drive_local_joint_channel:0", "one_qubit_drive_local_joint_channel",
       (0,), ("T2", "T1"), ("CTRL_1Q", "T2_T1_LOCAL"), ("T2", "T1"), (), R_1Q_LOCAL)]),
    ("one_qubit_drive_joint",
     lambda: _b(2).h(0),
     [("s0000:one_qubit_drive_joint_channel:0_1", "one_qubit_drive_joint_channel",
       (0, 1), ("T2", "T1", "T2_B", "T1_B"), ("CTRL_1Q", "T2_T1"),
       ("T2", "T1", "T2_B", "T1_B"), (), R_1Q_JOINT)]),
    ("one_qubit_drive_cluster",
     lambda: _b(3).h(0),
     [("s0000:one_qubit_drive_cluster_joint_channel:0_1_2", "one_qubit_drive_cluster_joint_channel",
       (0, 1, 2), ("T2", "T1", "T2_B", "T1_B"), ("CTRL_1Q", "T2_T1_CLUSTER"),
       ("T2", "T1", "T2_B", "T1_B"), (), R_1Q_CLUSTER)]),
    ("multi_one_qubit_drive_local",
     lambda: _b(2).h((0, 1)),
     [("s0000:multi_one_qubit_drive_local_joint_channel:0_1",
       "multi_one_qubit_drive_local_joint_channel", (0, 1), ("T2", "T1"),
       ("CTRL_1Q_LAYER", "T2_T1_LOCAL"), ("T2", "T1"), (), R_MULTI_1Q_LOCAL)]),
    ("multi_one_qubit_drive_cluster",
     lambda: _b(3).h((0, 1)),
     [("s0000:multi_one_qubit_drive_cluster_joint_channel:0_1_2",
       "multi_one_qubit_drive_cluster_joint_channel", (0, 1, 2), ("T2", "T1", "T2_B", "T1_B"),
       ("CTRL_1Q_LAYER", "T2_T1_CLUSTER"), ("T2", "T1", "T2_B", "T1_B"), (),
       R_MULTI_1Q_CLUSTER)]),
    ("one_qubit_drive_zz_joint",
     lambda: _b(2, zz=((0, 1),)).h(0),
     [("s0000:one_qubit_drive_zz_joint_channel:0_1", "one_qubit_drive_zz_joint_channel",
       (0, 1), ("ZZ", "T2", "T1", "T2_B", "T1_B"), ("CTRL_1Q", "ZZ"),
       ("T2", "T1", "T2_B", "T1_B"), ((0, 1),), R_1Q_ZZ_JOINT)]),
    ("multi_one_qubit_drive_zz_cluster",
     lambda: _b(3, zz=((0, 2),)).h((0, 1)),
     [("s0000:multi_one_qubit_drive_zz_cluster_joint_channel:0_1_2",
       "multi_one_qubit_drive_zz_cluster_joint_channel", (0, 1, 2),
       ("ZZ", "T2", "T1", "T2_B", "T1_B"), ("CTRL_1Q_LAYER", "ZZ_CLUSTER"),
       ("T2", "T1", "T2_B", "T1_B"), ((0, 2),), R_1Q_ZZ_CLUSTER)]),
    ("one_qubit_drive_zz_cluster",
     lambda: _b(3, zz=((1, 2),)).h(0),
     [("s0000:one_qubit_drive_zz_cluster_joint_channel:0_1_2",
       "one_qubit_drive_zz_cluster_joint_channel", (0, 1, 2),
       ("ZZ", "T2", "T1", "T2_B", "T1_B"), ("CTRL_1Q", "ZZ_CLUSTER"),
       ("T2", "T1", "T2_B", "T1_B"), ((1, 2),), R_1Q_ZZ_CLUSTER)]),
    ("idle_cluster",
     lambda: _b(1).idle(0, duration_ns=50.0),
     [("s0000:idle_cluster_joint_channel:0", "idle_cluster_joint_channel",
       (0,), ("T2", "T1"), ("IDLE", "T2_T1_CLUSTER"), ("T2", "T1"), (), R_IDLE_CLUSTER)]),
    ("idle_pair",
     lambda: _b(2).idle((0, 1), duration_ns=50.0),
     [("s0000:idle_pair_joint_channel:0_1", "idle_pair_joint_channel",
       (0, 1), ("T2", "T1", "T2_B", "T1_B"), ("T2_T1", "T2_T1"),
       ("T2", "T1", "T2_B", "T1_B"), (), R_IDLE_PAIR)]),
    ("idle_zz_cluster",
     lambda: _b(3, zz=((0, 1),)).idle((0, 1, 2), duration_ns=50.0),
     [("s0000:idle_zz_cluster_joint_channel:0_1_2", "idle_zz_cluster_joint_channel",
       (0, 1, 2), ("ZZ", "T2", "T1"), ("IDLE", "ZZ_CLUSTER"), ("T2", "T1"),
       ((0, 1),), R_IDLE_ZZ_CLUSTER)]),
    ("two_qubit_zz_noedge",
     lambda: _b(2).cz((0, 1)),
     [("s0000:two_qubit_zz_joint_channel:0_1", "two_qubit_zz_joint_channel",
       (0, 1), ("ZZ", "T2", "T1", "T2_B", "T1_B"), ("CTRL_CZ", "ZZ"),
       ("T2", "T1", "T2_B", "T1_B"), (), R_2Q_ZZ_NOEDGE)]),
    ("two_qubit_zz_edge",
     lambda: _b(2, zz=((0, 1),)).cz((0, 1)),
     [("s0000:two_qubit_zz_joint_channel:0_1", "two_qubit_zz_joint_channel",
       (0, 1), ("ZZ", "T2", "T1", "T2_B", "T1_B"), ("CTRL_CZ", "ZZ"),
       ("T2", "T1", "T2_B", "T1_B"), ((0, 1),), R_2Q_ZZ_EDGE)]),
    ("two_qubit_control_joint",
     lambda: _b(2).cx((0, 1)),
     [("s0000:two_qubit_control_joint_channel:0_1", "two_qubit_control_joint_channel",
       (0, 1), ("T2", "T1", "T2_B", "T1_B"), ("CTRL_CX", "T2_T1"),
       ("T2", "T1", "T2_B", "T1_B"), (), R_2Q_CTRL_JOINT_CX)]),
    ("two_qubit_control_cluster",
     lambda: _b(3).cz((0, 1)),
     [("s0000:two_qubit_control_cluster_joint_channel:0_1_2",
       "two_qubit_control_cluster_joint_channel", (0, 1, 2), ("T2", "T1", "T2_B", "T1_B"),
       ("CTRL_2Q_LAYER", "T2_T1_CLUSTER"), ("T2", "T1", "T2_B", "T1_B"), (), R_2Q_CLUSTER)]),
    ("two_qubit_control_zz_cluster",
     lambda: _b(3, zz=((0, 2),)).cz((0, 1)),
     [("s0000:two_qubit_control_zz_cluster_joint_channel:0_1_2",
       "two_qubit_control_zz_cluster_joint_channel", (0, 1, 2),
       ("ZZ", "T2", "T1", "T2_B", "T1_B"), ("CTRL_2Q_LAYER", "ZZ_CLUSTER"),
       ("T2", "T1", "T2_B", "T1_B"), ((0, 2),), R_2Q_ZZ_CLUSTER)]),
    ("readout_cluster",
     lambda: _b(1).measure((0,), key="m0", duration_ns=250.0),
     [("s0000:readout_cluster_joint_channel:0", "readout_cluster_joint_channel",
       (0,), ("RD", "T2", "T1"), ("READOUT", "T2_T1_CLUSTER"), ("T2", "T1"), (), R_RD_CLUSTER)]),
    ("readout_pair",
     lambda: _b(2).measure((0, 1), key=("m0", "m1"), duration_ns=250.0),
     [("s0000:readout_pair_joint_channel:0_1", "readout_pair_joint_channel",
       (0, 1), ("RD", "RD_B", "T2", "T1", "T2_B", "T1_B"), ("RD", "T2_T1"),
       ("RD_B", "T2", "T1", "T2_B", "T1_B"), (), R_RD_PAIR)]),
    ("readout_zz_cluster",
     lambda: _b(3, zz=((0, 1),)).measure((0, 1, 2), key=("m0", "m1", "m2"), duration_ns=250.0),
     [("s0000:readout_zz_cluster_joint_channel:0_1_2", "readout_zz_cluster_joint_channel",
       (0, 1, 2), ("ZZ", "RD", "T2", "T1", "T2_B", "T1_B"), ("READOUT", "ZZ_CLUSTER"),
       ("RD", "T2", "T1", "T2_B", "T1_B"), ((0, 1),), R_RD_ZZ_CLUSTER)]),
]


@pytest.mark.parametrize("case_id,builder,expected", _BATTERY,
                         ids=[c[0] for c in _BATTERY])
def test_L0_schedule_plan_rowkind_battery(case_id, builder, expected):
    plan = _schedule_plan(builder())
    assert plan.selector_id == AXIS1_SCHEDULE_SELECTOR_ID
    got = [_fields(s) for s in plan.selections]
    assert got == [tuple(e) for e in expected], case_id
    # every produced row_kind is in the supported set (structural guard invariant)
    for s in plan.selections:
        assert s.row_kind in AXIS1_SUPPORTED_SELECTION_ROW_KINDS


def test_L0_schedule_plan_rowkind_battery_has_teeth():
    # KILLER: the field pin must FAIL if a single field (here the row_kind) is sabotaged.
    plan = _schedule_plan(_b(2).cz((0, 1)))
    real = plan.selections[0]

    def prop(s):
        assert _fields(s)[1] == "two_qubit_zz_joint_channel"

    class _W:  # a sabotaged stand-in with a wrong row_kind
        selection_id = real.selection_id
        row_kind = "idle_cluster_joint_channel"
        participant = real.participant
        primitive_names = real.primitive_names
        mechanism_pair = real.mechanism_pair
        context_mechanisms = real.context_mechanisms
        coupling_edges = real.coupling_edges
        reason = real.reason

    assert_discriminates(prop, real, _W, label="schedule_plan row_kind")


# =========================================================================== #
# build_axis1_schedule_selection_plan -- to_manifest wiring on op shapes        #
# (pins _selection_from_substep's substep passthrough + Axis1MechanismSelection #
#  .to_manifest for the H / I-with-arg / M-with-basis-keys / coupling-edge cases)#
# =========================================================================== #
def test_L0_selection_to_manifest_one_qubit_drive_local():
    got = _schedule_plan(_b(1).h(0)).selections[0].to_manifest()
    assert got == {
        "selection_id": "s0000:one_qubit_drive_local_joint_channel:0",
        "row_kind": "one_qubit_drive_local_joint_channel", "substep_id": "s0000",
        "substep_kind": "one_qubit_gate", "participant": [0],
        "primitive_names": ["T2", "T1"], "mechanism_pair": ["CTRL_1Q", "T2_T1_LOCAL"],
        "context_mechanisms": ["T2", "T1"], "operation_names": ["H"],
        "source_step_indices": [0], "source_operation_ids": ["step:0"],
        "operations": [{"name": "H", "targets": [0], "source_step_index": 0, "args": []}],
        "dt_ns_nominal": 25.0, "dt_ns_bracket": [20.0, 30.0],
        "dt_source": "error_coupling_simulator.frontend.duration_policy.v1",
        "mechanism_slots": ["drive", "idle", "spectator"], "reason": R_1Q_LOCAL,
        "epistemic_class": "c",
    }


def test_L0_selection_to_manifest_idle_with_duration_arg():
    got = _schedule_plan(_b(1).idle(0, duration_ns=50.0)).selections[0].to_manifest()
    # the I op carries its explicit duration arg; dt_source/bracket flow from the substep.
    assert got["operations"] == [
        {"name": "I", "targets": [0], "source_step_index": 0, "args": [50.0]}]
    assert got["dt_ns_nominal"] == 50.0 and got["dt_ns_bracket"] == [50.0, 50.0]
    assert got["dt_source"] == "explicit_circuit_idle_duration"
    assert got["mechanism_slots"] == ["idle"] and got["reason"] == R_IDLE_CLUSTER


def test_L0_selection_to_manifest_measurement_basis_keys():
    got = _schedule_plan(
        _b(1).measure((0,), key="m0", duration_ns=250.0)).selections[0].to_manifest()
    assert got["operations"] == [{
        "name": "M", "targets": [0], "source_step_index": 0, "args": [250.0],
        "basis": "Z", "measurement_keys": ["m0"]}]
    assert got["dt_source"] == "explicit_circuit_measurement_duration"
    assert "coupling_edges" not in got                  # the falsy-edges arc: key ABSENT


def test_L0_selection_to_manifest_coupling_edges_present():
    got = _schedule_plan(_b(2, zz=((0, 1),)).h(0)).selections[0].to_manifest()
    # the truthy self.coupling_edges arc: the key is PRESENT as a list-of-lists.
    assert got["coupling_edges"] == [[0, 1]]

    def prop(m):
        assert m["coupling_edges"] == [[0, 1]]

    assert_discriminates(prop, got, {**got, "coupling_edges": [[0, 2]]},
                         label="selection.to_manifest coupling_edges")


# =========================================================================== #
# build_axis1_schedule_selection_plan -- context arc + skip/cluster arithmetic  #
# =========================================================================== #
def test_L0_schedule_plan_nontrivial_context_expands_primitives():
    # the `if not context.is_trivial:` TRUE arc: thermal-excitation context adds T1_UP/T1_UP_B
    # after every T1/T1_B, and the plan carries the context manifest.
    b = _b(2)
    b.declare_axis1_local_lindblad_context(
        {"include_thermal_excitation": True, "gamma_up_per_ns": 2.0e-4})
    b.h(0)
    plan = build_axis1_schedule_selection_plan(_sched(b))
    sel = plan.selections[0]
    assert sel.primitive_names == ("T2", "T1", "T1_UP", "T2_B", "T1_B", "T1_UP_B")
    assert sel.context_mechanisms == ("T2", "T1", "T1_UP", "T2_B", "T1_B", "T1_UP_B")
    m = plan.to_manifest()
    assert m["axis1_local_lindblad_context"]["include_thermal_excitation"] is True

    def prop(s):
        assert "T1_UP" in s.primitive_names

    assert_discriminates(prop, sel, _schedule_plan(_b(2).h(0)).selections[0],
                         label="thermal-context primitive expansion")


def test_L0_schedule_plan_trivial_context_no_context_key():
    # the `if not context.is_trivial:` FALSE arc + to_manifest's absent-context arc.
    plan = _schedule_plan(_b(2).h(0))
    assert plan.axis1_local_lindblad_context is None
    assert "axis1_local_lindblad_context" not in plan.to_manifest()


def test_L0_schedule_plan_unsupported_static_cluster_is_skipped():
    # window_support > max_support (5) WITH a declared static edge inside it -> the substep is
    # unsupported-cluster + skipped by every selector -> NO selection (kills the max_support
    # constant / the _unsupported_static_cluster arithmetic).
    for build in (
        lambda: _b(6, zz=((0, 5),)).idle((0, 1, 2, 3, 4, 5), duration_ns=50.0),
        lambda: _b(6, zz=((0, 5),)).h(0),
        lambda: _b(6, zz=((0, 5),)).measure(
            (0, 1, 2, 3, 4, 5), key=("m0", "m1", "m2", "m3", "m4", "m5"), duration_ns=250.0),
        # an oversized TWO-QUBIT substep with a declared static edge inside its support is added
        # to the unsupported-cluster skip set -> the cz-joint selector skips it too -> no rows.
        # (kills the two-qubit branch of _unsupported_static_cluster_substep_ids.)
        lambda: _b(6, zz=((0, 5),)).cz((0, 1)),
    ):
        assert _schedule_plan(build()).selections == ()
    # and with a leading reset (else-continue over an unhandled kind) the oversized two-qubit
    # substep is STILL added (kills the else `continue` -> `break` in that scan).
    assert _schedule_plan(_b(6, zz=((0, 5),)).reset(0).cz((0, 1))).selections == ()


def test_L0_schedule_plan_multi_pair_idle_and_readout():
    # >5 support with NO static -> not clustered, not unsupported -> the pair selectors run
    # their range(0, n, 2) / range(0, n-1, 2) loops multiple times (kills the loop-step mutants).
    idle6 = _schedule_plan(_b(6).idle((0, 1, 2, 3, 4, 5), duration_ns=50.0))
    assert [s.participant for s in idle6.selections] == [(0, 1), (2, 3), (4, 5)]
    assert {s.row_kind for s in idle6.selections} == {"idle_pair_joint_channel"}

    meas6 = _schedule_plan(
        _b(6).measure((0, 1, 2, 3, 4, 5),
                      key=("m0", "m1", "m2", "m3", "m4", "m5"), duration_ns=250.0))
    assert [s.participant for s in meas6.selections] == [(0, 1), (2, 3), (4, 5)]
    assert {s.row_kind for s in meas6.selections} == {"readout_pair_joint_channel"}


def test_L0_schedule_plan_two_qubit_crosswindow_and_activepair_zz_cluster():
    # cross-window static edge (no idle) -> two_qubit_control_zz_cluster via the cross-window arc.
    cross = _schedule_plan(_b(4, zz=((0, 2),)).cz((0, 1, 2, 3)))
    assert [_fields(s)[1:4] for s in cross.selections] == [
        ("two_qubit_control_zz_cluster_joint_channel", (0, 1, 2, 3), ("ZZ", "T2", "T1", "T2_B", "T1_B"))]
    assert cross.selections[0].coupling_edges == ((0, 2),)
    # non-CZ control on its own static active-pair (no idle, no cross-window) -> same row via the
    # `has_non_cz_control and active_pair_static_edges` arc.
    ap = _schedule_plan(_b(2, zz=((0, 1),)).cx((0, 1)))
    assert ap.selections[0].row_kind == "two_qubit_control_zz_cluster_joint_channel"
    assert ap.selections[0].coupling_edges == ((0, 1),)


def test_L0_schedule_plan_measX_and_reset_produce_nothing():
    # an X-basis measurement is skipped (basis != Z) and a reset substep has no selector.
    assert _schedule_plan(
        _b(1).measure((0,), key="m0", basis="X", duration_ns=250.0)).selections == ()
    assert _schedule_plan(_b(1).reset(0)).selections == ()


# =========================================================================== #
# build_axis1_joint_channel_selection_plan                                      #
# =========================================================================== #
def test_L0_joint_channel_plan_cz_and_drive():
    # full comparison plan: CZ exact-zero + H drive on a declared static-ZZ pair
    # (dr_zz_prediction_band). Order: _cz_exact_zero first, then _drive_zz.
    plan = _joint_channel_plan(_b(2, zz=((0, 1),)).h(0).cz((0, 1)))
    assert plan.selector_id == AXIS1_JOINT_CHANNEL_SELECTOR_ID
    assert [_fields(s) for s in plan.selections] == [
        ("s0001:zz_t2_exact_zero:0_1", "zz_t2_exact_zero", (0, 1), ("ZZ", "T2"),
         ("ZZ", "T2"), (), (), R_ZZ_T2_EXACT),
        ("s0000:dr_zz_prediction_band:0_1", "dr_zz_prediction_band", (0, 1),
         ("DR", "ZZ", "T2", "T1"), ("DR", "ZZ"), ("T2", "T1"), (), R_DR_ZZ),
    ]


def test_L0_joint_channel_plan_cz_only_no_static():
    # no static + no CX -> the CX-relabel guard is skipped; a lone CZ yields exactly zz_t2.
    plan = _joint_channel_plan(_b(2).cz((0, 1)))
    assert [_fields(s)[:2] for s in plan.selections] == [
        ("s0000:zz_t2_exact_zero:0_1", "zz_t2_exact_zero")]
    assert plan.static_zz_pairs == ()


def test_L0_joint_channel_plan_cx_without_static_raises():
    # not static_pairs AND a CX two-qubit gate -> the anti-relabel guard fires (exact message).
    _raises_exact(
        ValueError,
        "CX is not silently relabeled as CZ for Axis-1 joint-channel static-ZZ selection",
        lambda: _joint_channel_plan(_b(2).cx((0, 1))))


def test_L0_joint_channel_plan_cx_with_static_does_not_raise():
    # static present -> the `not static_pairs` operand is False -> NO raise (empty plan, no CZ,
    # no one-qubit drive). Kills the and->or mutant on the guard.
    plan = _joint_channel_plan(_b(3, zz=((0, 1),)).cx((0, 1)))
    assert plan.selections == ()
    assert plan.static_zz_pairs == ((0, 1),)


def test_L0_joint_channel_drive_zz_selected_and_skipped_pairs():
    # a single H(0) on 3 qubits with static (0,1): active=(0,), idle=(1,2). The (0,1) pair is a
    # declared static pair -> dr_zz selected; the (0,2) pair is NOT static -> `continue` skip.
    plan = _joint_channel_plan(_b(3, zz=((0, 1),)).h(0))
    assert [_fields(s)[:3] for s in plan.selections] == [
        ("s0000:dr_zz_prediction_band:0_1", "dr_zz_prediction_band", (0, 1))]


def test_L0_joint_channel_drive_zz_non_drive_gate_skipped():
    # a one-qubit control gate outside the comparison drive-name set is skipped; no
    # dr_zz row despite a declared static pair + an idle spectator.
    plan = _joint_channel_plan(_b(2, zz=((0, 1),)).gate("SQRT_Y", 0))
    assert plan.selections == ()


# =========================================================================== #
# Axis1MechanismSelection.__post_init__ -- coercion + every raise               #
# =========================================================================== #
def test_L0_selection_post_init_coercion():
    sel = Axis1MechanismSelection(
        selection_id=7, row_kind="idle_cluster_joint_channel", substep_id=3, substep_kind=9,
        participant=(0.0, 1.0, 2.0), primitive_names=("t2", 1),
        mechanism_pair=("idle", 2), context_mechanisms=("t2",),
        operation_names=("i", 3), source_step_indices=(0.0, 1.0),
        operation_records=({"name": "I"},), dt_ns_nominal=50, dt_ns_bracket=(50, 60),
        dt_source=123, mechanism_slots=("idle",), reason=456, coupling_edges=())
    assert sel.selection_id == "7" and type(sel.selection_id) is str
    assert sel.row_kind == "idle_cluster_joint_channel"
    assert sel.substep_id == "3" and sel.substep_kind == "9"
    assert sel.participant == (0, 1, 2) and all(type(q) is int for q in sel.participant)
    # str() coercion only -- NO .upper() (the redundant uppercasing was dropped: every
    # construction site passes ALL-CAPS literals, so it normalized nothing and MASKED the
    # helper-literal case-swap mutants the row_kind battery pins now kill). Lowercase strings
    # pass through unchanged; non-string entries are still str()-coerced.
    assert sel.primitive_names == ("t2", "1")
    assert sel.mechanism_pair == ("idle", "2")
    assert sel.context_mechanisms == ("t2",)
    assert sel.operation_names == ("i", "3")
    assert sel.source_step_indices == (0, 1) and all(type(i) is int for i in sel.source_step_indices)
    assert sel.dt_ns_nominal == 50.0 and type(sel.dt_ns_nominal) is float
    assert sel.dt_ns_bracket == (50.0, 60.0) and all(type(x) is float for x in sel.dt_ns_bracket)
    assert sel.dt_source == "123"
    assert sel.mechanism_slots == ("idle",)
    assert sel.reason == "456"
    # operation_records copied into plain dicts
    assert sel.operation_records == ({"name": "I"},)
    # nominal None arc
    assert _mk_sel(dt_ns_nominal=None).dt_ns_nominal is None


def test_L0_selection_post_init_participant_guards():
    _raises_exact(ValueError, "Axis-1 selection participant must contain at least one qubit",
                  lambda: _mk_sel(participant=()))
    _raises_exact(ValueError, "Axis-1 selection participant must contain distinct qubits",
                  lambda: _mk_sel(participant=(0, 0)))


def test_L0_selection_post_init_coupling_edge_guards():
    # a non-2-length raw edge (first edge loop)
    _raises_exact(ValueError, "invalid Axis-1 coupling edge (0, 1, 2)",
                  lambda: _mk_sel(participant=(0, 1, 2), coupling_edges=((0, 1, 2),)))
    # an equal-endpoint edge -> _normal_pair raises (its own message, BEFORE the redundant
    # in-loop re-check on line 153 -- proves line 153's raise is dead).
    _raises_exact(ValueError, "Axis-1 mechanism-selection pair must contain distinct qubits",
                  lambda: _mk_sel(participant=(0, 1), coupling_edges=((0, 0),)))
    # duplicate edges after normalization
    _raises_exact(ValueError, "Axis-1 selection coupling_edges must be unique",
                  lambda: _mk_sel(participant=(0, 1), coupling_edges=((0, 1), (1, 0))))
    # an edge not contained in participant
    _raises_exact(
        ValueError,
        "Axis-1 selection coupling_edges must be contained in participant; "
        "edge=(0, 2) participant=(0, 1)",
        lambda: _mk_sel(participant=(0, 1), coupling_edges=((0, 2),)))


def test_L0_selection_post_init_edges_only_valid_for_zz_or_pair_rows():
    # edges present on a non-zz/non-active-pair row_kind -> the "only valid for..." raise.
    _raises_exact(
        ValueError,
        "Axis-1 coupling_edges are currently only valid for static-ZZ union-support cluster "
        "selections or active CZ/ZZ pair provenance",
        lambda: _mk_sel(row_kind="idle_cluster_joint_channel", participant=(0, 1),
                        primitive_names=("T2", "T1"), coupling_edges=((0, 1),)))


def test_L0_selection_post_init_zz_cluster_requires_edges():
    _raises_exact(
        ValueError, "idle_zz_cluster_joint_channel requires coupling_edges",
        lambda: _mk_sel(row_kind="idle_zz_cluster_joint_channel", participant=(0, 1),
                        primitive_names=("ZZ", "T2", "T1"),
                        mechanism_pair=("IDLE", "ZZ_CLUSTER"), coupling_edges=()))


def test_L0_selection_post_init_zz_cluster_two_qubit_participant_ok():
    # a zz-cluster with EXACTLY two participants + its edge is VALID -> the `len(participant) < 2`
    # guard's FALSE arc (the only REACHABLE arc; see the line-181 dead-branch exemption + probe).
    sel = _mk_sel(row_kind="idle_zz_cluster_joint_channel", participant=(0, 1),
                  primitive_names=("ZZ", "T2", "T1"), mechanism_pair=("IDLE", "ZZ_CLUSTER"),
                  coupling_edges=((0, 1),))
    assert sel.coupling_edges == ((0, 1),) and sel.participant == (0, 1)


def test_L0_selection_post_init_active_pair_edges_must_equal_pair():
    # active-pair row with a 3-qubit participant -> edges != the participant pair -> raise
    # (the first `or` operand: len(participant) != 2).
    _raises_exact(
        ValueError,
        "two_qubit_zz_joint_channel coupling_edges must be exactly the selected participant pair",
        lambda: _mk_sel(row_kind="two_qubit_zz_joint_channel", participant=(0, 1, 2),
                        primitive_names=("ZZ", "T2", "T1"), mechanism_pair=("CTRL_CZ", "ZZ"),
                        coupling_edges=((0, 1),)))
    # the valid active-pair case (FALSE arc): 2 participants, edge == the pair.
    ok = _mk_sel(row_kind="two_qubit_zz_joint_channel", participant=(0, 1),
                 primitive_names=("ZZ", "T2", "T1"), mechanism_pair=("CTRL_CZ", "ZZ"),
                 coupling_edges=((0, 1),))
    assert ok.coupling_edges == ((0, 1),)


def test_L0_selection_post_init_remaining_field_guards():
    _raises_exact(ValueError, "unsupported Axis-1 selection row_kind 'bogus'",
                  lambda: _mk_sel(row_kind="bogus"))
    _raises_exact(ValueError, "Axis-1 selection requires at least one primitive",
                  lambda: _mk_sel(primitive_names=()))
    _raises_exact(ValueError, "Axis-1 selection mechanism_pair must have length 2",
                  lambda: _mk_sel(mechanism_pair=("ONLY_ONE",)))
    # dt bracket: low<0 (first `or` operand) / high<low (second operand)
    _raises_exact(ValueError, "invalid selection dt bracket (-1.0, 5.0)",
                  lambda: _mk_sel(dt_ns_bracket=(-1.0, 5.0)))
    _raises_exact(ValueError, "invalid selection dt bracket (5.0, 3.0)",
                  lambda: _mk_sel(dt_ns_bracket=(5.0, 3.0)))


# =========================================================================== #
# Axis1MechanismSelection.to_manifest -- edges-present vs edges-absent          #
# =========================================================================== #
def test_L0_selection_to_manifest_direct_edges_absent_and_present():
    plain = _mk_sel().to_manifest()
    assert "coupling_edges" not in plain
    assert plain["epistemic_class"] == "c"
    assert plain["source_operation_ids"] == ["step:0"]
    zz = _mk_sel(row_kind="idle_zz_cluster_joint_channel", participant=(0, 1),
                 primitive_names=("ZZ", "T2", "T1"), mechanism_pair=("IDLE", "ZZ_CLUSTER"),
                 coupling_edges=((0, 1),)).to_manifest()
    assert zz["coupling_edges"] == [[0, 1]]

    def prop(m):
        assert "coupling_edges" in m

    assert_discriminates(prop, zz, plain, label="to_manifest coupling_edges arc")


# =========================================================================== #
# Axis1MechanismSelectionPlan.__post_init__ / by_kind / require_kind / to_manifest #
# =========================================================================== #
def test_L0_plan_post_init_coercion_and_defaults():
    s = _mk_sel()
    plan = Axis1MechanismSelectionPlan(
        source_kind=5, source_hash=9, selections=[s],
        static_zz_pairs=((1, 0), (0, 1)))            # unnormalized + duplicate
    assert plan.source_kind == "5" and type(plan.source_kind) is str
    assert plan.source_hash == "9"
    assert isinstance(plan.selections, tuple) and plan.selections == (s,)
    assert plan.static_zz_pairs == ((0, 1),)         # normalized + sorted + de-duplicated
    assert plan.static_zz_calibrations == {}
    assert plan.selector_id == AXIS1_JOINT_CHANNEL_SELECTOR_ID  # default
    assert plan.schema == AXIS1_SELECTION_SCHEMA
    assert plan.axis1_local_lindblad_context is None  # None arc
    # dict-context arc
    plan2 = Axis1MechanismSelectionPlan(
        source_kind="k", source_hash="h", selections=(), static_zz_pairs=(),
        axis1_local_lindblad_context={"gamma_phi_per_ns": 1e-3})
    assert plan2.axis1_local_lindblad_context == {"gamma_phi_per_ns": 1e-3}


def test_L0_plan_post_init_empty_source_hash_raises():
    _raises_exact(ValueError, "Axis-1 selection plan requires source_hash",
                  lambda: Axis1MechanismSelectionPlan(
                      source_kind="k", source_hash="", selections=(), static_zz_pairs=()))


def test_L0_plan_by_kind_and_require_kind():
    plan = _joint_channel_plan(_b(2, zz=((0, 1),)).h(0).cz((0, 1)))
    assert [s.selection_id for s in plan.by_kind("zz_t2_exact_zero")] == [
        "s0001:zz_t2_exact_zero:0_1"]
    assert [s.selection_id for s in plan.by_kind("dr_zz_prediction_band")] == [
        "s0000:dr_zz_prediction_band:0_1"]
    assert plan.by_kind("readout_pair_joint_channel") == ()    # absent -> empty
    # require_kind returns the same rows for a present kind
    got = plan.require_kind("zz_t2_exact_zero")
    assert [s.selection_id for s in got] == ["s0001:zz_t2_exact_zero:0_1"]
    # require_kind raises for an absent kind (exact message)
    _raises_exact(ValueError, "Axis-1 selection plan has no 'nope' selection",
                  lambda: plan.require_kind("nope"))

    def prop(rows):
        assert len(rows) == 1 and rows[0].row_kind == "zz_t2_exact_zero"

    assert_discriminates(prop, plan.by_kind("zz_t2_exact_zero"),
                         plan.by_kind("dr_zz_prediction_band"), label="by_kind filter")


def test_L0_plan_to_manifest_exact_dict():
    b = _b(2, zz=((0, 1),))
    b.declare_static_zz_couplings(((0, 1),), zeta_rad_per_ns_by_edge={(0, 1): 0.25})
    b.h(0)
    b.cz((0, 1))
    plan = build_axis1_joint_channel_selection_plan(_sched(b))
    m = plan.to_manifest()
    assert m["schema"] == AXIS1_SELECTION_SCHEMA
    assert m["selector_id"] == AXIS1_JOINT_CHANNEL_SELECTOR_ID
    assert m["source_kind"] == "circuit_ir"
    assert m["source_hash"] == plan.source_hash and len(m["source_hash"]) == 64
    assert m["static_zz_pairs"] == [[0, 1]]
    assert m["static_zz_calibrations"] == [
        {"edge": [0, 1], "zeta_rad_per_ns": 0.25, "epistemic_class": "c"}]
    assert m["representability"] == "schedule_derived_axis1_selection_no_h_or_c_payload"
    assert m["scope"] == (
        "selection only; primitive lowering happens in "
        "error_coupling_simulator.mechanisms.axis1_primitives")
    assert m["selections"] == [s.to_manifest() for s in plan.selections]
    assert "axis1_local_lindblad_context" not in m       # no context declared

    def prop(mm):
        assert mm["static_zz_pairs"] == [[0, 1]]

    assert_discriminates(prop, m, {**m, "static_zz_pairs": [[0, 2]]},
                         label="plan.to_manifest static_zz_pairs")


def test_L0_plan_to_manifest_context_key_present():
    b = _b(2)
    b.declare_axis1_local_lindblad_context({"gamma_phi_per_ns": 1e-3})
    b.h(0)
    plan = build_axis1_schedule_selection_plan(_sched(b))
    m = plan.to_manifest()
    assert m["axis1_local_lindblad_context"] == dict(plan.axis1_local_lindblad_context)
    assert m["axis1_local_lindblad_context"]["gamma_phi_per_ns"] == 1e-3


# =========================================================================== #
# Axis1SelectionLayer.__post_init__ / participants / selection_ids / to_manifest #
# =========================================================================== #
def _two_disjoint_sels():
    a = _mk_sel(selection_id="a", participant=(0, 1))
    b = _mk_sel(selection_id="b", participant=(2, 3))
    return a, b


def test_L0_layer_post_init_coercion():
    # selections carry substep_id "0" so the coerced layer substep_id (int 0 -> "0") matches them.
    a = _mk_sel(selection_id="a", substep_id="0", participant=(0, 1))
    b = _mk_sel(selection_id="b", substep_id="0", participant=(2, 3))
    layer = Axis1SelectionLayer(substep_id=0, order_index=3.0, substep_kind=7, selections=[a, b])
    assert layer.substep_id == "0" and type(layer.substep_id) is str  # int -> str coercion
    assert layer.order_index == 3 and type(layer.order_index) is int  # float -> int coercion
    assert layer.substep_kind == "7"                                   # int -> str coercion
    assert isinstance(layer.selections, tuple) and layer.selections == (a, b)


def test_L0_layer_post_init_guards():
    _raises_exact(ValueError, "Axis-1 selection layer requires at least one selection",
                  lambda: Axis1SelectionLayer(
                      substep_id="s0000", order_index=0, substep_kind="idle", selections=()))
    # a selection whose substep_id differs from the layer's -> mismatch raise (exact message).
    other = _mk_sel(selection_id="x", substep_id="s0001", participant=(0,))
    _raises_exact(
        ValueError,
        "Axis-1 selection layer substep mismatch: layer='s0000' selection='s0001'",
        lambda: Axis1SelectionLayer(
            substep_id="s0000", order_index=0, substep_kind="idle", selections=(other,)))


def test_L0_layer_properties_and_manifest():
    a, b = _two_disjoint_sels()
    layer = Axis1SelectionLayer(
        substep_id="s0000", order_index=0, substep_kind="two_qubit_gate", selections=(a, b))
    assert layer.participants == ((0, 1), (2, 3))
    assert layer.selection_ids == ("a", "b")
    assert layer.to_manifest() == {
        "substep_id": "s0000", "order_index": 0, "substep_kind": "two_qubit_gate",
        "selection_ids": ["a", "b"],
        "row_kinds": ["idle_cluster_joint_channel", "idle_cluster_joint_channel"],
        "participants": [[0, 1], [2, 3]], "window_count": 2,
        "same_substep_semantics": "qubit_disjoint_parallel_windows_or_single_union_support",
    }

    def prop(L):
        assert L.participants == ((0, 1), (2, 3))

    wrong = Axis1SelectionLayer(
        substep_id="s0000", order_index=0, substep_kind="two_qubit_gate", selections=(a,))
    assert_discriminates(prop, layer, wrong, label="layer.participants")


# =========================================================================== #
# axis1_selection_layers_in_schedule_order + flatten + partition_manifest       #
# =========================================================================== #
def _recompute_layers(schedule, selections):
    """INDEPENDENT reimplementation of the partition contract (NOT a call into the module):
    group by substep_id, order substeps by schedule order_index, sort within by selection_id."""
    order = {ss.substep_id: int(ss.order_index) for ss in schedule.substeps}
    kind = {ss.substep_id: str(ss.kind) for ss in schedule.substeps}
    grouped: dict = {}
    for s in selections:
        grouped.setdefault(s.substep_id, []).append(s)
    out = []
    for sid in sorted(grouped, key=lambda x: order[x]):
        sels = sorted(grouped[sid], key=lambda s: s.selection_id)
        out.append((sid, order[sid], kind[sid],
                    tuple(s.selection_id for s in sels),
                    tuple(s.participant for s in sels)))
    return out


def test_L0_layers_partition_matches_independent_recompute():
    # 4q CZ(0,1,2,3) -> two disjoint two_qubit_zz windows in one substep; a 4q readout -> a
    # second layer. Ordered by schedule order_index.
    b = _b(4)
    b.cz((0, 1, 2, 3))
    b.measure((0, 1, 2, 3), key=("m0", "m1", "m2", "m3"), duration_ns=250.0)
    sched = _sched(b)
    plan = build_axis1_schedule_selection_plan(sched)
    layers = axis1_selection_layers_in_schedule_order(sched, plan.selections)
    got = [(L.substep_id, L.order_index, L.substep_kind, L.selection_ids, L.participants)
           for L in layers]
    assert got == _recompute_layers(sched, plan.selections)
    # structure sanity: 2 layers, first is the disjoint CZ pair layer.
    assert len(layers) == 2
    assert layers[0].substep_kind == "two_qubit_gate" and len(layers[0].selections) == 2
    assert layers[1].substep_kind == "measurement" and len(layers[1].selections) == 1

    def prop(g):
        assert g == _recompute_layers(sched, plan.selections)

    assert_discriminates(prop, got, got[::-1], label="schedule-ordered layers")


def test_L0_layers_custom_consumer_name_default_ok():
    # the default consumer_name path: a clean disjoint partition must not raise.
    b = _b(4).cz((0, 1, 2, 3))
    sched = _sched(b)
    sels = build_axis1_schedule_selection_plan(sched).selections
    layers = axis1_selection_layers_in_schedule_order(
        sched, sels, consumer_name="Custom-consumer")
    assert len(layers) == 1 and len(layers[0].selections) == 2


def test_L0_layers_unknown_substep_raises():
    # a selection referencing a substep absent from the schedule.
    sched = _sched(_b(1).h(0))
    stray = _mk_sel(selection_id="ghost", substep_id="s9999", participant=(0,))
    _raises_exact(ValueError, "selection 'ghost' references unknown substep",
                  lambda: axis1_selection_layers_in_schedule_order(sched, (stray,)))


def test_L0_layers_empty_participant_guard_both_consumer_names():
    # the empty-participant guard is reachable only by forcing an already-built selection's
    # participant to () (the __post_init__ forbids it at construction). substep_id must be a
    # real schedule substep so the unknown-substep guard passes first.
    sched = _sched(_b(1).h(0))
    sel = _mk_sel(selection_id="s", substep_id="s0000", participant=(0,))
    object.__setattr__(sel, "participant", ())
    _raises_exact(
        ValueError,
        "Axis-1 selected-window evidence requires local windows with at least one "
        "participants; got ()",
        lambda: axis1_selection_layers_in_schedule_order(sched, (sel,)))
    _raises_exact(
        ValueError,
        "Consumer-X requires local windows with at least one participants; got ()",
        lambda: axis1_selection_layers_in_schedule_order(
            sched, (sel,), consumer_name="Consumer-X"))


def test_L0_layers_overlap_guard_both_consumer_names():
    # two same-substep selections with OVERLAPPING support -> the qubit-disjoint guard fires.
    sched = _sched(_b(3).h(0))                          # substep s0000 exists
    a = _mk_sel(selection_id="a", substep_id="s0000", participant=(0, 1))
    c = _mk_sel(selection_id="c", substep_id="s0000", participant=(1, 2))  # overlaps on qubit 1
    _raises_exact(
        ValueError,
        "Axis-1 selected-window evidence supports same-substep selections only when "
        "their supports are qubit-disjoint; overlapping selected window(s) on 's0000': "
        "participant=(1, 2) overlap=[1]",
        lambda: axis1_selection_layers_in_schedule_order(sched, (a, c)))
    _raises_exact(
        ValueError,
        "Consumer-Y supports same-substep selections only when "
        "their supports are qubit-disjoint; overlapping selected window(s) on 's0000': "
        "participant=(1, 2) overlap=[1]",
        lambda: axis1_selection_layers_in_schedule_order(
            sched, (a, c), consumer_name="Consumer-Y"))


def test_L0_flatten_layers():
    b = _b(4)
    b.cz((0, 1, 2, 3))
    b.measure((0, 1, 2, 3), key=("m0", "m1", "m2", "m3"), duration_ns=250.0)
    sched = _sched(b)
    plan = build_axis1_schedule_selection_plan(sched)
    layers = axis1_selection_layers_in_schedule_order(sched, plan.selections)
    flat = flatten_axis1_selection_layers(layers)
    # flattening preserves layer order then within-layer order
    expected = tuple(s for L in layers for s in L.selections)
    assert flat == expected
    assert [s.selection_id for s in flat] == [
        "s0000:two_qubit_zz_joint_channel:0_1",
        "s0000:two_qubit_zz_joint_channel:2_3",
        "s0001:readout_cluster_joint_channel:0_1_2_3"]


def test_L0_partition_manifest_exact_dict():
    b = _b(4)
    b.cz((0, 1, 2, 3))
    b.measure((0, 1, 2, 3), key=("m0", "m1", "m2", "m3"), duration_ns=250.0)
    sched = _sched(b)
    plan = build_axis1_schedule_selection_plan(sched)
    layers = axis1_selection_layers_in_schedule_order(sched, plan.selections)
    man = axis1_selection_partition_manifest(layers)
    assert man == {
        "schema": AXIS1_SELECTION_PARTITION_SCHEMA,
        "layer_count": 2,
        "selection_count": 3,
        "supports_are_qubit_disjoint_within_each_substep": True,
        "layer_order": "schedule_order_index_then_selection_id",
        "same_substep_semantics": "qubit_disjoint_parallel_windows_or_single_union_support",
        "layers": [L.to_manifest() for L in layers],
        "epistemic_class": "a",
    }
    # counts are the load-bearing values
    assert_pins({"layers": man["layer_count"], "sels": man["selection_count"]},
                {"layers": 2, "sels": 3}, label="partition counts")

    def prop(m):
        assert m["selection_count"] == 3

    assert_discriminates(prop, man, {**man, "selection_count": 2},
                         label="partition_manifest selection_count")


def test_L0_partition_manifest_empty_layers():
    man = axis1_selection_partition_manifest(())
    assert man["layer_count"] == 0 and man["selection_count"] == 0 and man["layers"] == []


FEAT_THERMAL = "computational-subspace thermal excitation primitives"
FEAT_FSIM = "computational-subspace fSim residual Hamiltonian primitives"


# =========================================================================== #
# _selection_with_lindblad_context + _fsim_residual_primitives_for_selection    #
# (the non-trivial-context primitive/reason expansion on two-qubit selections)  #
# =========================================================================== #
def test_L0_context_thermal_and_fsim_on_two_qubit_zz():
    b = _b(2)
    b.declare_axis1_local_lindblad_context({
        "include_thermal_excitation": True, "gamma_up_per_ns": 2.0e-4,
        "include_fsim_residual": True, "fsim_delta_theta_rad": 0.1, "fsim_delta_phi_rad": 0.2})
    b.cz((0, 1))
    sel = build_axis1_schedule_selection_plan(_sched(b)).selections[0]
    # thermal inserts T1_UP after T1 and T1_UP_B after T1_B; fSim appends SWAP+PHASE.
    assert sel.primitive_names == (
        "ZZ", "T2", "T1", "T1_UP", "T2_B", "T1_B", "T1_UP_B", "FSIM_SWAP", "FSIM_PHASE")
    assert sel.context_mechanisms == (
        "T2", "T1", "T1_UP", "T2_B", "T1_B", "T1_UP_B", "FSIM_SWAP", "FSIM_PHASE")
    assert sel.reason == (
        R_2Q_ZZ_NOEDGE + "; public Axis1LocalLindbladContextSpec selects "
        + FEAT_THERMAL + " and " + FEAT_FSIM)

    def prop(s):
        assert "FSIM_PHASE" in s.primitive_names

    assert_discriminates(prop, sel, _schedule_plan(_b(2).cz((0, 1))).selections[0],
                         label="fSim residual primitive expansion")


def test_L0_context_fsim_theta_only_on_cx():
    # only delta_theta != 0 -> FSIM_SWAP appended, no FSIM_PHASE; the row is in the fSim set.
    b = _b(2)
    b.declare_axis1_local_lindblad_context(
        {"include_fsim_residual": True, "fsim_delta_theta_rad": 0.1})
    b.cx((0, 1))
    sel = build_axis1_schedule_selection_plan(_sched(b)).selections[0]
    assert sel.primitive_names == ("T2", "T1", "T2_B", "T1_B", "FSIM_SWAP")
    assert sel.reason == R_2Q_CTRL_JOINT_CX + (
        "; public Axis1LocalLindbladContextSpec selects " + FEAT_FSIM)


def test_L0_context_fsim_on_non_two_qubit_returns_unchanged():
    # fSim residual context on an IDLE selection: substep_kind != two_qubit_gate -> _fsim
    # returns (); primitives unchanged -> _selection_with_lindblad_context early-returns the
    # SAME selection (reason unchanged).
    b = _b(1)
    b.declare_axis1_local_lindblad_context(
        {"include_fsim_residual": True, "fsim_delta_phi_rad": 0.2})
    b.idle(0, duration_ns=50.0)
    sel = build_axis1_schedule_selection_plan(_sched(b)).selections[0]
    assert sel.primitive_names == ("T2", "T1")
    assert sel.reason == R_IDLE_CLUSTER              # NOT extended (early return)


def test_L0_context_preserves_coupling_edges():
    # a thermal context on a selection that CARRIES coupling_edges -> the rebuilt selection
    # must preserve them (kills the mutant that drops coupling_edges=selection.coupling_edges).
    b = _b(2, zz=((0, 1),))
    b.declare_axis1_local_lindblad_context(
        {"include_thermal_excitation": True, "gamma_up_per_ns": 2.0e-4})
    b.h(0)
    sel = build_axis1_schedule_selection_plan(_sched(b)).selections[0]
    assert sel.coupling_edges == ((0, 1),)
    assert sel.primitive_names == ("ZZ", "T2", "T1", "T1_UP", "T2_B", "T1_B", "T1_UP_B")


# =========================================================================== #
# branch-execution + boundary kills for the generic selectors                   #
# =========================================================================== #
def test_L0_allactive_zz_cluster_has_no_B_primitives():
    # 3 all-active H with a static edge -> zz-cluster with has_idle=False -> the ELSE tuple
    # ("ZZ","T2","T1") (no _B), exercising the no-idle ternary arc.
    sel = _schedule_plan(_b(3, zz=((0, 1),)).h((0, 1, 2))).selections[0]
    assert sel.row_kind == "multi_one_qubit_drive_zz_cluster_joint_channel"
    assert sel.participant == (0, 1, 2) and sel.coupling_edges == ((0, 1),)
    assert sel.primitive_names == ("ZZ", "T2", "T1")
    assert sel.context_mechanisms == ("T2", "T1")


def test_L0_boundary_active_gt_one_at_support_two():
    # active==2, support==2 with a static edge -> enters the cluster branch via the
    # `len(active_qubits) > 1` operand (kills `> 1` -> `> 2`).
    sel = _schedule_plan(_b(2, zz=((0, 1),)).h((0, 1))).selections[0]
    assert sel.row_kind == "multi_one_qubit_drive_zz_cluster_joint_channel"
    assert sel.participant == (0, 1) and sel.coupling_edges == ((0, 1),)


def test_L0_readout_cluster_with_idle_has_B_primitives():
    # a Z readout with an idle spectator -> the idle-branch primitives (with _B) + context.
    sel = _schedule_plan(
        _b(3).measure((0, 1), key=("m0", "m1"), duration_ns=250.0)).selections[0]
    assert sel.row_kind == "readout_cluster_joint_channel"
    assert sel.primitive_names == ("RD", "T2", "T1", "T2_B", "T1_B")
    assert sel.context_mechanisms == ("T2", "T1", "T2_B", "T1_B")


def test_L0_boundary_support_exactly_max_is_not_skipped():
    # window_support == MAX_SUPPORT (5) is NOT skipped (kills `> MAX` -> `>= MAX`) across the
    # one-qubit / two-qubit / idle / readout cluster selectors.
    drive5 = _schedule_plan(_b(5, zz=((0, 4),)).h(0)).selections
    assert drive5 and drive5[0].participant == (0, 1, 2, 3, 4)
    assert drive5[0].row_kind == "one_qubit_drive_zz_cluster_joint_channel"
    idle5 = _schedule_plan(_b(5).idle((0, 1, 2, 3, 4), duration_ns=50.0)).selections
    assert idle5 and idle5[0].participant == (0, 1, 2, 3, 4)
    read5 = _schedule_plan(
        _b(5).measure((0, 1, 2, 3, 4), key=("m0", "m1", "m2", "m3", "m4"),
                      duration_ns=250.0)).selections
    assert read5 and read5[0].participant == (0, 1, 2, 3, 4)
    # two-qubit cluster at support 5: CZ(0,1) with 3 idle spectators.
    tq5 = _schedule_plan(_b(5).cz((0, 1))).selections
    assert tq5 and tq5[0].participant == (0, 1, 2, 3, 4)
    assert tq5[0].row_kind == "two_qubit_control_cluster_joint_channel"
    # multi-active drive at support 5 (the `> MAX` guard inside the multi-active branches).
    ma5 = _schedule_plan(_b(5).h((0, 1))).selections
    assert ma5 and ma5[0].participant == (0, 1, 2, 3, 4)
    assert ma5[0].row_kind == "multi_one_qubit_drive_cluster_joint_channel"
    # single-active drive at support 5 (the `<= MAX` guard in the single-active idle branch).
    sa5 = _schedule_plan(_b(5).h(0)).selections
    assert sa5 and sa5[0].participant == (0, 1, 2, 3, 4)
    assert sa5[0].row_kind == "one_qubit_drive_cluster_joint_channel"


def test_L0_no_duration_measurement_yields_no_readout():
    # a measurement WITHOUT an explicit duration has dt_ns_nominal=None -> every readout
    # selector skips it (kills the `or ... is None` -> `and` guard).
    assert _schedule_plan(_b(1).measure((0,), key="m0")).selections == ()


def test_L0_frontend_two_qubit_ordered_pairs_multi():
    # a 4-target CX -> two ordered control windows (0,1) and (2,3); kills the range-step and
    # the targets[i+1] index mutants in _operation_pair_participants_ordered.
    sels = _schedule_plan(_b(4).cx((0, 1, 2, 3))).selections
    assert [(s.row_kind, s.participant) for s in sels] == [
        ("two_qubit_control_joint_channel", (0, 1)),
        ("two_qubit_control_joint_channel", (2, 3))]


def test_L0_static_pair_needs_both_endpoints_in_support():
    # a static edge with only ONE endpoint in an idle substep's support must be EXCLUDED
    # (kills the `and` -> `or` mutant in _static_pairs_within_support; the `or` variant would
    # attach a (0,3) edge to a (0,1,2) participant and raise at Axis1MechanismSelection).
    sel = _schedule_plan(
        _b(4, zz=((0, 3),)).idle((0, 1, 2), duration_ns=50.0)).selections[0]
    assert sel.row_kind == "idle_cluster_joint_channel"   # NOT idle_zz_cluster
    assert sel.coupling_edges == ()


# =========================================================================== #
# multi-substep grand tour: continue -> break kills across the selector bank    #
# =========================================================================== #
def test_L0_grand_tour_multisubstep_every_producer_survives():
    # reset (skipped by every selector) FIRST, then a one-qubit / two-qubit / idle /
    # measurement substep -> each selector's leading `if kind != X: continue` MUST skip the
    # reset (and other kinds) and still reach its own producing substep. A `break` mutant
    # stops at the first skip -> the later producer's selection vanishes -> killed.
    b = _b(4)
    b.reset(0)
    b.h(0)
    b.cz((0, 1))
    b.idle((0, 1, 2, 3), duration_ns=50.0)
    b.measure((0, 1, 2, 3), key=("m0", "m1", "m2", "m3"), duration_ns=250.0)
    plan = build_axis1_schedule_selection_plan(_sched(b))
    by_substep = {s.substep_id: s.row_kind for s in plan.selections}
    assert by_substep == {
        "s0001": "one_qubit_drive_cluster_joint_channel",
        "s0002": "two_qubit_control_cluster_joint_channel",
        "s0003": "idle_cluster_joint_channel",
        "s0004": "readout_cluster_joint_channel",
    }


def test_L0_joint_channel_grand_tour_cz_then_drive_order():
    # Comparison path: reset, CZ (zz_t2), then H drive on a static pair (dr_zz). The
    # _cz_exact_zero and _drive_zz loops must both skip the reset and reach their producers.
    b = _b(2, zz=((0, 1),))
    b.reset(0)
    b.cz((0, 1))
    b.h(0)
    plan = build_axis1_joint_channel_selection_plan(_sched(b))
    assert {(s.substep_id, s.row_kind) for s in plan.selections} == {
        ("s0001", "zz_t2_exact_zero"), ("s0002", "dr_zz_prediction_band")}


# =========================================================================== #
# NONE-arg / value pins on the schedule-plan wiring                             #
# =========================================================================== #
def test_L0_schedule_plan_source_fields_pinned():
    # kills the mutants replacing source_kind/source_hash/static_zz_calibrations with None
    # in build_axis1_schedule_selection_plan's Plan(...) call.
    b = _b(2, zz=((0, 1),))
    b.declare_static_zz_couplings(((0, 1),), zeta_rad_per_ns_by_edge={(0, 1): 0.25})
    b.cz((0, 1))
    sched = _sched(b)
    plan = build_axis1_schedule_selection_plan(sched)
    assert plan.source_kind == "circuit_ir" == sched.source_kind
    assert plan.source_hash == sched.source_hash and len(plan.source_hash) == 64
    assert plan.static_zz_calibrations == {
        (0, 1): {"zeta_rad_per_ns": 0.25, "epistemic_class": "c"}}


def test_L0_validate_drive_slots_message_via_joint_channel():
    # Force a one-qubit substep to carry wrong slots; the comparison selector's
    # _validate_drive_slots raise fires with the EXACT message (kills the message None/case/XX
    # and the sorted(None) mutants).
    sched = _sched(_b(2).h(0))
    object.__setattr__(sched.substeps[0], "mechanism_slots", ("wrong",))
    _raises_exact(
        ValueError,
        "Axis-1 joint-channel drive selection requires one-qubit drive mechanism slots "
        "['drive', 'idle', 'spectator'], got ['wrong'] on 's0000'",
        lambda: build_axis1_joint_channel_selection_plan(sched))


def test_L0_selection_with_context_full_manifest():
    # pin the FULL to_manifest of a context-REBUILT selection: every field is copied from the
    # source selection (kills the mutants that null selection_id/substep_id/substep_kind/
    # dt_ns_nominal/dt_source when _selection_with_lindblad_context reconstructs the record).
    b = _b(2)
    b.declare_axis1_local_lindblad_context(
        {"include_thermal_excitation": True, "gamma_up_per_ns": 2.0e-4})
    b.cz((0, 1))
    got = build_axis1_schedule_selection_plan(_sched(b)).selections[0].to_manifest()
    assert got == {
        "selection_id": "s0000:two_qubit_zz_joint_channel:0_1",
        "row_kind": "two_qubit_zz_joint_channel", "substep_id": "s0000",
        "substep_kind": "two_qubit_gate", "participant": [0, 1],
        "primitive_names": ["ZZ", "T2", "T1", "T1_UP", "T2_B", "T1_B", "T1_UP_B"],
        "mechanism_pair": ["CTRL_CZ", "ZZ"],
        "context_mechanisms": ["T2", "T1", "T1_UP", "T2_B", "T1_B", "T1_UP_B"],
        "operation_names": ["CZ"], "source_step_indices": [0],
        "source_operation_ids": ["step:0"],
        "operations": [{"name": "CZ", "targets": [0, 1], "source_step_index": 0, "args": []}],
        "dt_ns_nominal": 30.0, "dt_ns_bracket": [25.0, 45.0],
        "dt_source": "error_coupling_simulator.frontend.duration_policy.v1",
        "mechanism_slots": ["two_qubit_drive", "zz_spectator", "idle"],
        "reason": R_2Q_ZZ_NOEDGE + "; public Axis1LocalLindbladContextSpec selects " + FEAT_THERMAL,
        "epistemic_class": "c",
    }


def _rows(plan):
    return [s.row_kind for s in plan.selections]


def test_L0_multi_producer_break_kills_inner_continues():
    # MEGA schedule: each producing substep KIND appears multiple times, separated by other
    # kinds. Each selector loop must process EVERY same-kind producer; a `break` (mutated
    # `continue`) after the first producer drops the later ones -> the substep->row map breaks.
    b = _b(4)
    b.reset(0); b.h(0); b.cz((0, 1)); b.h(1); b.cz((2, 3))
    b.idle((0, 1), duration_ns=50.0); b.h(2)
    b.idle((0, 1, 2), duration_ns=50.0)
    b.measure((0,), key="m0", duration_ns=250.0); b.h(3)
    b.measure((1, 2), key=("m1", "m2"), duration_ns=250.0)
    plan = build_axis1_schedule_selection_plan(_sched(b))
    got = {s.substep_id: s.row_kind for s in plan.selections}
    assert got == {
        "s0001": "one_qubit_drive_cluster_joint_channel",
        "s0002": "two_qubit_control_cluster_joint_channel",
        "s0003": "one_qubit_drive_cluster_joint_channel",
        "s0004": "two_qubit_control_cluster_joint_channel",
        "s0005": "idle_pair_joint_channel",
        "s0006": "one_qubit_drive_cluster_joint_channel",
        "s0007": "idle_cluster_joint_channel",
        "s0008": "readout_cluster_joint_channel",
        "s0009": "one_qubit_drive_cluster_joint_channel",
        "s0010": "readout_cluster_joint_channel",
    }


def test_L0_multi_producer_branch_doubles():
    # per-branch double producers (skip substep between) so a break in that branch's path
    # drops the second producer. Each pins EXACTLY two selections of the branch's row_kind.
    # drive LOCAL (1q, no idle):
    assert _rows(_schedule_plan(_b(1).h(0).reset(0).h(0))) == [
        "one_qubit_drive_local_joint_channel"] * 2
    # two_qubit CZ/ZZ joint (2q, no idle):
    assert _rows(_schedule_plan(_b(2).cz((0, 1)).reset(0).cz((0, 1)))) == [
        "two_qubit_zz_joint_channel"] * 2
    # frontend two-qubit control (2q CX, no idle):
    assert _rows(_schedule_plan(_b(2).cx((0, 1)).reset(0).cx((0, 1)))) == [
        "two_qubit_control_joint_channel"] * 2
    # idle PAIR (2q):
    assert _rows(_schedule_plan(
        _b(2).idle((0, 1), duration_ns=50.0).reset(0).idle((0, 1), duration_ns=60.0))) == [
        "idle_pair_joint_channel"] * 2
    # readout PAIR (2q):
    assert _rows(_schedule_plan(
        _b(2).measure((0, 1), key=("m0", "m1"), duration_ns=250.0).reset((0, 1))
        .measure((0, 1), key=("m2", "m3"), duration_ns=250.0))) == [
        "readout_pair_joint_channel"] * 2
    # readout CLUSTER (2q, single measured + idle spectator):
    assert _rows(_schedule_plan(
        _b(2).measure((0,), key="m0", duration_ns=250.0).reset(0)
        .measure((1,), key="m1", duration_ns=250.0))) == [
        "readout_cluster_joint_channel"] * 2
    # idle CLUSTER (3q):
    assert _rows(_schedule_plan(
        _b(3).idle((0, 1, 2), duration_ns=50.0).reset(0)
        .idle((0, 1, 2), duration_ns=60.0))) == ["idle_cluster_joint_channel"] * 2
    # drive ZZ-joint (2q, single idle spectator, static pair):
    assert _rows(_schedule_plan(
        _b(2, zz=((0, 1),)).h(0).reset(0).h(0))) == [
        "one_qubit_drive_zz_joint_channel"] * 2


def test_L0_joint_channel_multi_producer_break():
    # Comparison path: reset, CZ, H(drive), reset, CZ; both CZs and the H are selected.
    b = _b(3, zz=((0, 1),))
    b.reset(0); b.cz((0, 1)); b.h(0); b.reset(1); b.cz((0, 1))
    plan = build_axis1_joint_channel_selection_plan(_sched(b))
    assert {(s.substep_id, s.row_kind) for s in plan.selections} == {
        ("s0001", "zz_t2_exact_zero"), ("s0002", "dr_zz_prediction_band"),
        ("s0004", "zz_t2_exact_zero")}


def test_L0_operation_pair_participants_odd_target_raises():
    # a hand-forced odd-target two-qubit op reaches _operation_pair_participants' odd-count
    # raise (via build_axis1_schedule_selection_plan on the schedule) with the EXACT message.
    from error_coupling_simulator.frontend.analog_schedule import SubstepOperation
    sched = _sched(_b(2).cx((0, 1)))
    bad = SubstepOperation("CX", (0, 1, 2), 0)
    object.__setattr__(sched.substeps[0], "operations", (bad,))
    _raises_exact(ValueError, "CX operation has odd target count: (0, 1, 2)",
                  lambda: build_axis1_schedule_selection_plan(sched))
    # A CZ odd-target op reaches the same helper via the comparison path.
    sched2 = _sched(_b(2).cz((0, 1)))
    object.__setattr__(sched2.substeps[0], "operations", (SubstepOperation("CZ", (0, 1, 2), 0),))
    _raises_exact(ValueError, "CZ operation has odd target count: (0, 1, 2)",
                  lambda: build_axis1_joint_channel_selection_plan(sched2))


def test_L0_frontend_two_qubit_ordered_overlap_raises():
    # a hand-forced OVERLAPPING ordered pair reaches _operation_pair_participants_ordered's
    # overlap raise (exact message). NB the repeated-endpoint (a==b) route is UNREACHABLE via
    # build_*: _generic_two_qubit_layer_cluster_selections runs FIRST and its
    # _two_qubit_operation_pairs -> _operation_pair_participants -> _normal_pair rejects a==b
    # ("...pair must contain distinct qubits") before the ordered helper is ever reached; the
    # overlap route survives because _operation_pair_participants does NOT check overlap, and a
    # no-idle 2q substep is not claimed by the cluster selector so the ordered helper runs.
    from error_coupling_simulator.frontend.analog_schedule import SubstepOperation
    sched = _sched(_b(4).cx((0, 1, 2, 3)))
    object.__setattr__(sched.substeps[0], "operations",
                       (SubstepOperation("CX", (0, 1, 1, 2), 0),))
    _raises_exact(ValueError, "CX operation has overlapping pair target(s): (0, 1, 1, 2)",
                  lambda: build_axis1_schedule_selection_plan(sched))


def test_L0_context_fsim_on_two_qubit_cluster_rows():
    # fSim residual applies to the two_qubit_control_(zz_)cluster rows too (kills the mutants on
    # those row-kind entries of the _fsim_residual_primitives_for_selection allowlist).
    b = _b(3)
    b.declare_axis1_local_lindblad_context(
        {"include_fsim_residual": True, "fsim_delta_theta_rad": 0.1})
    b.cz((0, 1))
    sel = build_axis1_schedule_selection_plan(_sched(b)).selections[0]
    assert sel.row_kind == "two_qubit_control_cluster_joint_channel"
    assert sel.primitive_names == ("T2", "T1", "T2_B", "T1_B", "FSIM_SWAP")
    b = _b(3, zz=((0, 2),))
    b.declare_axis1_local_lindblad_context(
        {"include_fsim_residual": True, "fsim_delta_theta_rad": 0.1})
    b.cz((0, 1))
    sel = build_axis1_schedule_selection_plan(_sched(b)).selections[0]
    assert sel.row_kind == "two_qubit_control_zz_cluster_joint_channel"
    assert sel.primitive_names == ("ZZ", "T2", "T1", "T2_B", "T1_B", "FSIM_SWAP")


def test_L0_static_zz_calibrations_undeclared_edge_raises():
    # force an undeclared static-ZZ calibration onto a schedule -> _static_zz_calibrations'
    # normalize raise fires with the EXACT label-carrying message (kills the label None/case/XX
    # and declared_edges=None mutants).
    sched = _sched(_b(2).cz((0, 1)))
    object.__setattr__(sched, "static_zz_calibrations", {(0, 1): {"zeta_rad_per_ns": 0.1}})
    _raises_exact(
        ValueError,
        "SubstepSchedule.static_zz_calibrations[0] edge (0, 1) is not declared in "
        "axis1_static_zz_couplings",
        lambda: build_axis1_schedule_selection_plan(sched))


def test_L0_drive_branch_doubles():
    # per-branch double producers for the remaining _generic_drive_selections branches, so a
    # `break` in the branch path drops the later producer.
    assert _rows(_schedule_plan(_b(2).h(0).reset(0).h(0))) == [
        "one_qubit_drive_joint_channel"] * 2                         # single idle spectator
    assert _rows(_schedule_plan(_b(3).h(0).reset(0).h(0))) == [
        "one_qubit_drive_cluster_joint_channel"] * 2                 # multi idle spectator
    assert _rows(_schedule_plan(_b(2).h((0, 1)).reset(0).h((0, 1)))) == [
        "multi_one_qubit_drive_local_joint_channel"] * 2            # multi-active, no idle
    assert _rows(_schedule_plan(_b(3).h((0, 1)).reset(0).h((0, 1)))) == [
        "multi_one_qubit_drive_cluster_joint_channel"] * 2          # multi-active + idle
    assert _rows(_schedule_plan(
        _b(4, zz=((0, 3),)).h(0).reset(0).h(0))) == [
        "one_qubit_drive_zz_cluster_joint_channel"] * 2            # zz-cluster branch


def test_L0_remaining_branch_doubles():
    # the zz-cluster / control-cluster branch doubles not covered above (each a [produce; reset;
    # produce] so a `break` in the branch path drops the second producer).
    assert _rows(_schedule_plan(
        _b(3, zz=((0, 2),)).h((0, 1)).reset(2).h((0, 1)))) == [
        "multi_one_qubit_drive_zz_cluster_joint_channel"] * 2
    assert _rows(_schedule_plan(_b(3).cz((0, 1)).reset(2).cz((0, 1)))) == [
        "two_qubit_control_cluster_joint_channel"] * 2
    assert _rows(_schedule_plan(
        _b(3, zz=((0, 2),)).cz((0, 1)).reset(2).cz((0, 1)))) == [
        "two_qubit_control_zz_cluster_joint_channel"] * 2
    assert _rows(_schedule_plan(
        _b(3, zz=((0, 1),)).idle((0, 1, 2), duration_ns=50.0).reset(2)
        .idle((0, 1, 2), duration_ns=60.0))) == ["idle_zz_cluster_joint_channel"] * 2
    assert _rows(_schedule_plan(
        _b(3, zz=((0, 1),)).measure((0, 1, 2), key=("m0", "m1", "m2"), duration_ns=250.0)
        .reset(2).measure((0, 1, 2), key=("m3", "m4", "m5"), duration_ns=250.0))) == [
        "readout_zz_cluster_joint_channel"] * 2


def test_L0_skip_set_continue_doubles():
    # a CLUSTERED two-qubit substep (in the skip set) followed by a cz-joint two-qubit substep:
    # the cz-joint / frontend selectors must SKIP the clustered one (their `substep_id in
    # skip_substep_ids: continue`) and still reach the later producer -> a break drops it.
    plan = build_axis1_schedule_selection_plan(
        _sched(_b(4).cz((0, 1)).reset((2, 3)).cz((0, 1, 2, 3))))
    by = {}
    for s in plan.selections:
        by.setdefault(s.substep_id, []).append(s.row_kind)
    assert by["s0000"] == ["two_qubit_control_cluster_joint_channel"]  # clustered
    assert by["s0002"] == ["two_qubit_zz_joint_channel", "two_qubit_zz_joint_channel"]  # cz-joint
    # a CLUSTERED CX (idle spectators) + a frontend-control CX pair -> frontend skip-set continue.
    plan2 = build_axis1_schedule_selection_plan(
        _sched(_b(4).cx((0, 1)).reset((2, 3)).cx((0, 1, 2, 3))))
    by2 = {}
    for s in plan2.selections:
        by2.setdefault(s.substep_id, []).append(s.row_kind)
    assert by2["s0000"] == ["two_qubit_control_cluster_joint_channel"]
    assert by2["s0002"] == ["two_qubit_control_joint_channel", "two_qubit_control_joint_channel"]


def test_L0_layers_partition_single_qubit_selection_no_raise():
    # a len-1-participant selection must PASS the `< 1` guard (kills `< 1` -> `<= 1` / `< 2`,
    # which would raise on a legitimate single-qubit window).
    sched = _sched(_b(1).h(0))
    sels = build_axis1_schedule_selection_plan(sched).selections
    assert sels[0].participant == (0,)
    layers = axis1_selection_layers_in_schedule_order(sched, sels)
    assert len(layers) == 1 and layers[0].participants == ((0,),)


# =========================================================================== #
# L1 properties (Hypothesis)                                                    #
# =========================================================================== #
_ROWS_NO_EDGE = sorted(AXIS1_SUPPORTED_SELECTION_ROW_KINDS - {
    "idle_zz_cluster_joint_channel", "multi_one_qubit_drive_zz_cluster_joint_channel",
    "one_qubit_drive_zz_cluster_joint_channel", "readout_zz_cluster_joint_channel",
    "two_qubit_control_zz_cluster_joint_channel", "one_qubit_drive_zz_joint_channel",
    "two_qubit_zz_joint_channel"})


@settings(max_examples=100, deadline=None)
@given(qubits=st.lists(st.integers(0, 12), min_size=1, max_size=5, unique=True),
       row=st.sampled_from(_ROWS_NO_EDGE))
def test_L1_selection_manifest_roundtrip_no_edges(qubits, row):
    part = tuple(qubits)
    sel = _mk_sel(row_kind=row, participant=part, primitive_names=("T2", "T1"),
                  mechanism_pair=("A", "B"))
    m = sel.to_manifest()
    # participant round-trips as a list; distinctness + count preserved; no edge key.
    assert m["participant"] == list(part)
    assert m["row_kind"] == row
    assert "coupling_edges" not in m
    assert m["epistemic_class"] == "c"


@settings(max_examples=100, deadline=None)
@given(n=st.integers(1, 3), extra=st.integers(0, 2))
def test_L1_schedule_plan_selection_ids_unique_and_well_formed(n, extra):
    # any single one-qubit-gate schedule yields exactly one selection whose id encodes its
    # substep + row + participant; ids are unique across the plan.
    total = n + extra
    b = CircuitBuilder(total)
    b.h(tuple(range(n)))
    plan = build_axis1_schedule_selection_plan(_sched(b))
    ids = [s.selection_id for s in plan.selections]
    assert len(ids) == len(set(ids))
    for s in plan.selections:
        assert s.selection_id.startswith(s.substep_id + ":" + s.row_kind + ":")
        assert s.selection_id.endswith("_".join(str(q) for q in s.participant))


# =========================================================================== #
# OPTION-A gap closures -- three workflow-verified L2 gaps in the private helper #
# bank that the row_kind battery could not reach (the .upper() de-dup un-masks   #
# the helper-literal case-swap mutants; these close the remaining reachable ones)#
# =========================================================================== #
def test_L0_unsupported_static_cluster_max_support_is_reached_not_none():
    # GAP 1: _unsupported_static_cluster_substep_ids evaluates `len(support) > max_support`
    # for EACH substep kind. A mutant that sets max_support=None makes `len(support) > None`
    # raise TypeError instead of returning a set. The from_spec=False canonical schedule carries
    # a one_qubit_gate / two_qubit_gate / idle / measurement substep, so every kind-branch is
    # reached; past the early `if not static_pairs: return` guard (non-empty static_pairs) and
    # with no oversized support the ORIGINAL returns set() while each None-mutant raises -> killed.
    from error_coupling_simulator.frontend.axis1_selection import (
        _unsupported_static_cluster_substep_ids,
    )
    sched = canonical_sealed_schedule(from_spec=False)
    assert _unsupported_static_cluster_substep_ids(
        sched, static_pairs=frozenset({(0, 1)})) == set()


def test_L0_frontend_two_qubit_ordered_repeated_pair_raises_and_nonrepeated_builds():
    # GAP 2: _operation_pair_participants_ordered's repeated-pair (`a == b`) raise. The
    # layer-cluster helper's support cap (>5) skips a substep BEFORE its
    # _two_qubit_operation_pairs -> _normal_pair would reject a==b, so a >5-support two-qubit
    # SWAP(0,0) substep reaches the ORDERED helper with a repeated pair. The ORIGINAL raises its
    # OWN exact message; the `a == b`->`a != b` mutant does not raise there (and the built
    # selection's duplicate participant then raises a DIFFERENT message) and the message->None
    # mutant raises `ValueError(None)` -- both fail the exact pin.
    from error_coupling_simulator.frontend.analog_schedule import SubstepOperation
    sched = _sched(_b(7).cz((0, 1)))                 # active=(0,1), idle=(2..6), support 7 > 5
    object.__setattr__(sched.substeps[0], "operations",
                       (SubstepOperation("SWAP", (0, 0), 0),))
    assert_raises_exact(
        ValueError, "SWAP operation has repeated pair target: (0, 0)",
        lambda: build_axis1_schedule_selection_plan(sched))
    # the `a != b` direction (the flipped mutant would raise here instead): a real ordered SWAP
    # pair builds exactly one two_qubit_control_joint_channel window.
    plan = _schedule_plan(_b(2).gate("SWAP", (0, 1)))
    assert [(s.row_kind, s.participant, s.mechanism_pair) for s in plan.selections] == [
        ("two_qubit_control_joint_channel", (0, 1), ("CTRL_SWAP", "T2_T1"))]


def test_L0_layers_ordered_by_order_index_not_substep_id_string():
    # GAP 3: axis1_selection_layers_in_schedule_order orders layers by the schedule's
    # order_index, NOT by substep_id string. Real compiled schedules always emit monotonic ids
    # ("s0000","s0001",...) so string order == order_index order and a `sorted(grouped,
    # key=None)` (or a `key=lambda item: None`) mutant is invisible. Two substeps whose
    # substep_id string order is the REVERSE of their order_index expose it; passing the
    # selections in string order (insertion order s_aaa, s_zzz) also breaks the
    # stable-insertion-order variant. ORIGINAL -> [s_zzz(0), s_aaa(1)]; both mutants -> [s_aaa,
    # s_zzz].
    from types import SimpleNamespace
    fake_sched = SimpleNamespace(substeps=(
        SimpleNamespace(substep_id="s_zzz", order_index=0, kind="idle"),
        SimpleNamespace(substep_id="s_aaa", order_index=1, kind="idle"),
    ))
    sel_z = _mk_sel(selection_id="z", substep_id="s_zzz", participant=(0,))
    sel_a = _mk_sel(selection_id="a", substep_id="s_aaa", participant=(1,))
    layers = axis1_selection_layers_in_schedule_order(fake_sched, (sel_a, sel_z))
    assert [L.substep_id for L in layers] == ["s_zzz", "s_aaa"]
    assert [L.order_index for L in layers] == [0, 1]

    def prop(ls):
        assert [L.substep_id for L in ls] == ["s_zzz", "s_aaa"]

    assert_discriminates(prop, layers, tuple(reversed(layers)),
                         label="layers ordered by order_index not substep_id string")


# --------------------------------------------------------------------------- #
# OPTION-A adversarial-reachability closures: four MORE private-helper mutants  #
# proven REACHABLE (constructed a reaching input, diffed orig-vs-mutant) --      #
# genuine gaps, NOT equivalents, so closed rather than classified away.          #
# --------------------------------------------------------------------------- #
def test_L0_frontend_two_qubit_ordered_odd_target_raises_reaching_input():
    # _operation_pair_participants_ordered's ODD-count raise is normally preempted by
    # _operation_pair_participants (inside the layer-cluster helper's _two_qubit_operation_pairs)
    # -- but a >5-support two-qubit substep skips that helper BEFORE it runs, so a 3-target
    # frontend op reaches the ORDERED helper's own odd-count raise. ORIGINAL raises the exact
    # message; the message->None mutant raises ValueError(None).
    from error_coupling_simulator.frontend.analog_schedule import SubstepOperation
    sched = _sched(_b(7).cz((0, 1)))                 # support 7 > 5 skips the cluster helper
    object.__setattr__(sched.substeps[0], "operations",
                       (SubstepOperation("SWAP", (0, 1, 2), 0),))
    assert_raises_exact(
        ValueError, "SWAP operation has odd target count: (0, 1, 2)",
        lambda: build_axis1_schedule_selection_plan(sched))


def test_L0_static_pairs_within_support_needs_first_endpoint_too():
    # _static_pairs_within_support tests BOTH endpoints. A static edge whose MAX endpoint is in a
    # support but MIN endpoint is NOT must be EXCLUDED. Edge (1,3) on an idle window over (2,3):
    # 3 in support, 1 NOT -> excluded -> a plain idle_pair (no coupling edge). The
    # `int(pair[0])`->`int(pair[1])` mutant tests 3 twice, INCLUDES (1,3), and then
    # Axis1MechanismSelection raises (edge endpoint 1 not in participant (2,3)).
    plan = _schedule_plan(_b(4, zz=((1, 3),)).idle((2, 3), duration_ns=50.0))
    assert [(s.row_kind, s.participant, s.coupling_edges) for s in plan.selections] == [
        ("idle_pair_joint_channel", (2, 3), ())]


def test_L0_idle_joint_channel_odd_over_cap_support_yields_no_pairs():
    # _generic_idle_joint_channel_selections' `< 2 or ... % 2` skip drops ODD idle counts before
    # the range(0, n, 2) pair loop. A 7-qubit idle with NO static edge is over the cluster cap
    # (>5, not clustered) and reaches the pair selector with an ODD count; the ORIGINAL skips it.
    # The `or`->`and` mutant would NOT skip and would index past the tuple end (IndexError).
    assert _schedule_plan(
        _b(7).idle((0, 1, 2, 3, 4, 5, 6), duration_ns=50.0)).selections == ()


def test_L0_multi_active_no_idle_support_exactly_max_not_skipped():
    # _generic_drive_selections' multi-active-no-idle support cap: support == MAX (5) is NOT
    # skipped. Five all-active H with no idle -> multi_one_qubit_drive_local over (0,1,2,3,4). The
    # `> MAX`->`>= MAX` mutant on this branch skips it (5 >= 5) and produces nothing.
    plan = _schedule_plan(_b(5).h((0, 1, 2, 3, 4)))
    assert [(s.row_kind, s.participant) for s in plan.selections] == [
        ("multi_one_qubit_drive_local_joint_channel", (0, 1, 2, 3, 4))]
