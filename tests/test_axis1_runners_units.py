"""Stage-D batch ``axis1_runners`` (D9) -- per-unit L0+L1 coverage of the two frontend CPU
fixture builders (docs/SIMULATOR.md D9):

  * ``error_coupling_simulator.frontend.axis1_codespec_runner`` (5 public units)
  * ``error_coupling_simulator.frontend.joint_channel_comparison_runner``        (3 public units)

Both modules are pure orchestration: they construct a frontend ``CodeSpec`` / ``SubstepSchedule``
via the CPU compiler (analog_schedule / code_spec / circuit_ir) and then drive the GPU
record/evidence emitters + freeze guards. NEITHER imports torch/quimb, so no unit is gpu_bound;
the GPU work lives in ``axis1_record_evidence`` / ``joint_channel_comparison`` behind
``write_axis1_measurement_record_evidence`` / ``write_joint_channel_comparison_evidence`` (both route into
``_require_cuda_device`` -- device='cpu' raises "GPU-only"). The units' OWN bodies are covered on
CPU by monkeypatching those GPU-callee writers (and, for ``main``, the ``run_*`` fixture itself) at
the runner-module boundary; the ``build_*_spec`` / ``build_*_schedule`` compilers run REAL on CPU.

L0 -- 100% statement + branch per unit. The three ``build_*`` builders are straight-line CodeSpec /
schedule construction (branch 0/0). ``run_*`` carries the ``write_freeze`` IfExp (both arcs);
``main`` carries parse_args(argv is None) + ``validate_freeze is not None`` + summary-freeze IfExp +
``passed`` return-IfExp (all arcs exercised).

L1 -- faithfulness PROPERTIES: a VALID CodeSpec / sealed SubstepSchedule is constructed (checks
reference real ancillae/data, logical commutes + is validated by __post_init__, order_index is
sealed sequential, compiler seal is valid), and the emitted schedule matches what the spec declares.

VALUE-PINS (the standing lesson): every construction is pinned against an INDEPENDENT recompute from
the fixture inputs -- the CodeSpec fields, the round-by-round measurement_keys / detectors /
observables, the deterministic record_layout_hash + source_hash (sha256 identity; catches every
metadata/qubit/gate mutation incl. the joint-channel static-ZZ edge and H/CZ targets), and main's summary dict
recomputed field-by-field from a distinct-valued fake manifest. ``assert_discriminates`` shows the
round-count pin FAILS on a dropped/added round and the layout pin FAILS on the 4q vs 5q spec.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from _support.faithfulness import assert_discriminates

from error_coupling_simulator.frontend import axis1_codespec_runner as cr
from error_coupling_simulator.frontend import joint_channel_comparison_runner as gr
from error_coupling_simulator.frontend.analog_schedule import (
    SubstepSchedule,
    has_valid_compiler_schedule_seal,
)
from error_coupling_simulator.frontend.code_spec import CodeSpec

# --------------------------------------------------------------------------- #
# Independent recompute of the compiled record layout (from the fixture design, #
# NOT the module's builder) -- the DISCRIMINATING pins.                         #
# --------------------------------------------------------------------------- #
def _expected_measurement_keys(rounds: int) -> list[str]:
    """The 5q mixed-basis fixture: two ancilla reads per round (x0 X-check, z1 Z-check) plus the
    three final data measurements (q0:X for the x0 seam, q1:Z, q2:Z the logical). Recomputed from
    the declared checks/logicals, not by re-running the compiler."""
    keys: list[str] = []
    for r in range(rounds):
        keys += [f"round{r}:x0", f"round{r}:z1"]
    keys += ["final:q0:X", "final:q1:Z", "final:q2:Z"]
    return keys


def _expected_detectors(rounds: int) -> list[dict]:
    """delta detectors pair consecutive same-check ancilla reads (rounds 1..R-1); the two final
    detectors pair the last ancilla read with its final data read. z-coord = round index (delta) or
    R (final) -- the fixture's declared check coords (x0 at (0.0,0.5), z1 at (1.0,0.5))."""
    dets: list[dict] = []
    for r in range(1, rounds):
        dets.append({"name": f"delta:x0:round{r}", "keys": [f"round{r - 1}:x0", f"round{r}:x0"],
                     "coords": [0.0, 0.5, float(r)]})
        dets.append({"name": f"delta:z1:round{r}", "keys": [f"round{r - 1}:z1", f"round{r}:z1"],
                     "coords": [1.0, 0.5, float(r)]})
    dets.append({"name": "final:x0", "keys": [f"round{rounds - 1}:x0", "final:q0:X"],
                 "coords": [0.0, 0.5, float(rounds)]})
    dets.append({"name": "final:z1", "keys": [f"round{rounds - 1}:z1", "final:q1:Z"],
                 "coords": [1.0, 0.5, float(rounds)]})
    return dets


_EXPECTED_OBSERVABLES = [{"name": "logical_z2", "keys": ["final:q2:Z"], "index": 0}]


def _dump(d: dict) -> str:
    """The EXACT bytes ``main`` prints -- json.dumps(indent=2, sort_keys=True) + the print newline.
    Pinning the RAW stdout (not json.loads) is what discriminates the indent/sort_keys kwargs of the
    print (a parsed-dict compare is blind to them)."""
    return json.dumps(d, indent=2, sort_keys=True) + "\n"

# deterministic sha256 identities (class-a exact) of the frozen fixtures -- pinned so ANY
# metadata / qubit / gate / round mutation that changes the compiled circuit is caught.
_CODESPEC_R2_SOURCE_HASH = "8c27ac8f1e90050de000523a2e0a87d1ef758b00ba369d804cb0610ceb89e239"
_CODESPEC_R2_LAYOUT_HASH = "0f23786bec35c459bf06783e7308ea0cdcf64388bd6ccad2a70c9133d30404f4"
_CODESPEC_R3_SOURCE_HASH = "697ef8192968ecf3ee8aa4bfc9f2b4efcde55a6968aed839e49ed889810c4d06"
_CODESPEC_R3_LAYOUT_HASH = "38bd4db893ab6c2690db6406ac592eae3c2a9211c7c599e20f941672c6b69ee1"
_JOINT_CHANNEL_SOURCE_HASH = "f8a47a5cb18d1e257b5ec533f4c4479b348d07b0fb4cc76ba0de29bed885a07c"


# --------------------------------------------------------------------------- #
# Fake GPU-callee results (SimpleNamespace) -- the CPU seam.                    #
# --------------------------------------------------------------------------- #
def _fake_codespec_evidence(*, passed: bool = True) -> SimpleNamespace:
    """A stand-in for Axis1MeasurementRecordEvidenceResult with DISTINCT numeric fields so a
    key-swap mutation in main's summary (record_count <-> applied_channel_count <-> key count)
    diverges."""
    manifest = {
        "record_evidence": {
            "record_count": 7,
            "measurement_keys": ["a", "b", "c"],  # len 3
            "applied_channel_count": 4,
            "measurement_basis": "mixed_pauli",
        },
        "coverage": {"full_positive_duration_coverage": True},
        "verdict": "pass" if passed else "fail",
        "passed": passed,
        "source_kind": "code_spec_compiler",
        "source_hash": "deadbeefsource",
    }
    return SimpleNamespace(
        out_dir=Path("fake/out/dir"),
        record_evidence=Path("fake/out/dir/axis1_measurement_records.json"),
        content_hash="contenthash123",
        manifest=manifest,
    )


def _fake_codespec_result(*, passed: bool = True, with_freeze: bool = True) -> SimpleNamespace:
    freeze = SimpleNamespace(freeze_path=Path("fake/out/dir/records.freeze.json")) if with_freeze else None
    return SimpleNamespace(spec=None, schedule=None, evidence=_fake_codespec_evidence(passed=passed),
                           freeze=freeze)


def _fake_joint_channel_evidence(*, passed: bool = True) -> SimpleNamespace:
    manifest = {
        "rows": [1, 2, 3, 4, 5],  # len 5
        "verdict": "pass" if passed else "fail",
        "passed": passed,
        "source_kind": "circuit_ir",
        "source_hash": "deadbeef_joint_channel",
    }
    return SimpleNamespace(
        out_dir=Path("fake/comparison/dir"),
        joint_channel_comparison=Path("fake/comparison/dir/joint_channel_comparison.json"),
        content_hash="jointchannelhash456",
        manifest=manifest,
    )


def _fake_joint_channel_result(*, passed: bool = True, with_freeze: bool = True) -> SimpleNamespace:
    freeze = SimpleNamespace(freeze_path=Path("fake/comparison/dir/joint_channel_comparison.freeze.json")) if with_freeze else None
    return SimpleNamespace(schedule=None, evidence=_fake_joint_channel_evidence(passed=passed), freeze=freeze)


# =========================================================================== #
# codespec_runner: build_axis1_codespec_frontend_spec (L0 + L1 + value pins)   #
# =========================================================================== #
def _pin_5q_spec_fields(spec: CodeSpec, *, rounds: int) -> None:
    """Pin EVERY declared field of the 5q mixed-basis fixture against the design (independent of
    the builder). A flipped index / dropped qubit / mis-set coord / renamed check FAILS a pin."""
    assert spec.name == "axis1_codespec_mixed_basis_frontend"
    assert spec.num_qubits == 5
    assert spec.data_indices == (0, 1, 2)
    assert spec.ancilla_indices == (3, 4)
    assert [(q.index, q.coords) for q in spec.data_qubits] == [(0, (0.0,)), (1, (1.0,)), (2, (2.0,))]
    assert [(q.index, q.coords) for q in spec.ancilla_qubits] == [(3, (0.0, 0.5)), (4, (1.0, 0.5))]
    assert [(c.name, c.ancilla, [(t.qubit, t.basis) for t in c.terms], c.coords) for c in spec.checks] == [
        ("x0", 3, [(0, "X")], (0.0, 0.5)),
        ("z1", 4, [(1, "Z")], (1.0, 0.5)),
    ]
    assert [(o.name, o.index, [(t.qubit, t.basis) for t in o.terms]) for o in spec.logical_observables] == [
        ("logical_z2", 0, [(2, "Z")]),
    ]
    assert spec.rounds == rounds
    assert spec.metadata == {"fixture": "axis1_codespec_record_frontend",
                             "encoded_distance_certified": False}


def test_L0_build_5q_spec_default_and_rounds():
    _pin_5q_spec_fields(cr.build_axis1_codespec_frontend_spec(), rounds=2)          # default rounds=2
    _pin_5q_spec_fields(cr.build_axis1_codespec_frontend_spec(rounds=3), rounds=3)  # threaded rounds


def test_L0_build_4q_spec_default_and_rounds():
    """The registered 4q coupled-process variant: 3 data + 1 X-check ancilla."""
    assert cr.build_axis1_codespec_4q_frontend_spec().rounds == 2   # default rounds=2
    for rounds in (2, 3):
        s = cr.build_axis1_codespec_4q_frontend_spec(rounds=rounds)
        assert s.name == "axis1_codespec_4q_frontend"
        assert s.num_qubits == 4
        assert s.data_indices == (0, 1, 2)
        assert s.ancilla_indices == (3,)
        assert [(q.index, q.coords) for q in s.data_qubits] == [(0, (0.0,)), (1, (1.0,)), (2, (2.0,))]
        assert [(q.index, q.coords) for q in s.ancilla_qubits] == [(3, (0.0, 0.5))]
        assert [(c.name, c.ancilla, [(t.qubit, t.basis) for t in c.terms], c.coords) for c in s.checks] == [
            ("x0", 3, [(0, "X")], (0.0, 0.5)),
        ]
        assert [(o.name, o.index, [(t.qubit, t.basis) for t in o.terms]) for o in s.logical_observables] == [
            ("logical_z2", 0, [(2, "Z")]),
        ]
        assert s.rounds == rounds
        assert s.metadata == {"fixture": "axis1_codespec_4q_frontend",
                              "encoded_distance_certified": False}


def test_L1_specs_are_valid_codespecs():
    """FAITHFULNESS: both builders return VALID CodeSpecs -- __post_init__ validated commuting
    checks, in-range qubits, and a logical NOT in the stabilizer span (construction success is the
    invariant). Independently re-assert the membership relations."""
    for spec in (cr.build_axis1_codespec_frontend_spec(), cr.build_axis1_codespec_4q_frontend_spec()):
        assert isinstance(spec, CodeSpec)
        data = set(spec.data_indices)
        anc = set(spec.ancilla_indices)
        assert data.isdisjoint(anc)
        assert data | anc <= set(range(spec.num_qubits))
        for c in spec.checks:
            assert c.ancilla in anc
            assert all(t.qubit in data for t in c.terms)
        for o in spec.logical_observables:
            assert all(t.qubit in data for t in o.terms)


def test_DISCRIMINATES_layout_pin_bites_4q_vs_5q():
    """The 5q-layout pin has teeth: it HOLDS for the 5q spec and FAILS for the 4q spec (a
    mis-sized layout / dropped z1 check)."""
    def prop(spec):
        assert spec.num_qubits == 5
        assert {c.name for c in spec.checks} == {"x0", "z1"}
    assert_discriminates(prop, cr.build_axis1_codespec_frontend_spec(),
                         cr.build_axis1_codespec_4q_frontend_spec(), label="5q_layout")


# =========================================================================== #
# codespec_runner: build_axis1_codespec_frontend_schedule                      #
# =========================================================================== #
def _pin_codespec_schedule(sch: SubstepSchedule, *, rounds: int, source_hash: str, layout_hash: str) -> None:
    assert isinstance(sch, SubstepSchedule)
    assert sch.num_qubits == 5
    assert sch.source_kind == "code_spec_compiler"
    assert has_valid_compiler_schedule_seal(sch) is True
    assert all(su.generated_by_compiler for su in sch.substeps)
    rl = sch.record_layout_ref
    assert rl["measurement_keys"] == _expected_measurement_keys(rounds)
    assert rl["detectors"] == _expected_detectors(rounds)
    assert rl["observables"] == _EXPECTED_OBSERVABLES
    # deterministic sha256 identities pin the whole compiled circuit + layout.
    assert sch.source_hash == source_hash
    assert rl["record_layout_hash"] == layout_hash


def test_L0_build_codespec_schedule_default_and_rounds():
    _pin_codespec_schedule(cr.build_axis1_codespec_frontend_schedule(), rounds=2,
                           source_hash=_CODESPEC_R2_SOURCE_HASH, layout_hash=_CODESPEC_R2_LAYOUT_HASH)
    _pin_codespec_schedule(cr.build_axis1_codespec_frontend_schedule(rounds=3), rounds=3,
                           source_hash=_CODESPEC_R3_SOURCE_HASH, layout_hash=_CODESPEC_R3_LAYOUT_HASH)


def test_DISCRIMINATES_round_count_pin_bites_dropped_round():
    """The measurement-key pin fails when a round is dropped/added: it HOLDS for the rounds=2
    schedule and FAILS for the rounds=3 schedule."""
    def prop(sch):
        assert sch.record_layout_ref["measurement_keys"] == _expected_measurement_keys(2)
    assert_discriminates(prop, cr.build_axis1_codespec_frontend_schedule(rounds=2),
                         cr.build_axis1_codespec_frontend_schedule(rounds=3), label="round_count")


# =========================================================================== #
# codespec_runner: run_axis1_codespec_record_fixture (GPU callee monkeypatched) #
# =========================================================================== #
def _patch_codespec_writers(monkeypatch):
    calls: dict = {}
    fake_ev = _fake_codespec_evidence()
    fake_frz = SimpleNamespace(freeze_path=Path("fake/out/dir/records.freeze.json"))

    def fake_write(schedule, out_dir, *, device="cuda"):
        calls["write"] = {"schedule": schedule, "out_dir": out_dir, "device": device}
        return fake_ev

    def fake_freeze(record_evidence, *, overwrite=False):
        calls["freeze"] = {"record_evidence": record_evidence, "overwrite": overwrite}
        return fake_frz

    monkeypatch.setattr(cr, "write_axis1_measurement_record_evidence", fake_write)
    monkeypatch.setattr(cr, "freeze_axis1_measurement_record_evidence", fake_freeze)
    return calls, fake_ev, fake_frz


def test_L0_run_codespec_fixture_defaults_freeze_on(monkeypatch):
    """write_freeze default True arc: builds the REAL 5q spec+schedule (CPU), threads defaults to the
    (mocked) GPU writer, freezes with overwrite=refresh_freeze default False, wires the result."""
    calls, fake_ev, fake_frz = _patch_codespec_writers(monkeypatch)
    res = cr.run_axis1_codespec_record_fixture("some/out")
    # real CPU-built spec + schedule threaded correctly (default rounds=2)
    assert isinstance(res.spec, CodeSpec) and res.spec.num_qubits == 5 and res.spec.rounds == 2
    assert isinstance(res.schedule, SubstepSchedule) and res.schedule.source_kind == "code_spec_compiler"
    # writer call: the compiled schedule + out_dir + default device
    assert calls["write"]["schedule"] is res.schedule
    assert calls["write"]["out_dir"] == "some/out"
    assert calls["write"]["device"] == "cuda"
    # freeze call: evidence.record_evidence + overwrite=refresh_freeze default False
    assert calls["freeze"]["record_evidence"] == fake_ev.record_evidence
    assert calls["freeze"]["overwrite"] is False
    # result wiring
    assert res.evidence is fake_ev
    assert res.freeze is fake_frz


def test_L0_run_codespec_fixture_explicit_args_freeze_off(monkeypatch):
    """write_freeze False arc: freeze NEVER called, result.freeze is None; explicit args threaded."""
    calls, fake_ev, _ = _patch_codespec_writers(monkeypatch)
    res = cr.run_axis1_codespec_record_fixture("x/y", rounds=3, device="cpu",
                                               write_freeze=False, refresh_freeze=True)
    assert res.spec.rounds == 3
    assert calls["write"]["out_dir"] == "x/y"
    assert calls["write"]["device"] == "cpu"
    assert "freeze" not in calls          # freeze branch NOT taken
    assert res.freeze is None


def test_L0_run_codespec_fixture_threads_refresh_freeze(monkeypatch):
    """overwrite=refresh_freeze is threaded (True arc distinct from the default False)."""
    calls, _, _ = _patch_codespec_writers(monkeypatch)
    cr.run_axis1_codespec_record_fixture("z", refresh_freeze=True)
    assert calls["freeze"]["overwrite"] is True


# =========================================================================== #
# codespec_runner: main                                                        #
# =========================================================================== #
def _expected_codespec_summary(result: SimpleNamespace) -> dict:
    """Independent recompute of the summary main must print (field-by-field from the manifest)."""
    ev = result.evidence
    rec = ev.manifest["record_evidence"]
    cov = ev.manifest["coverage"]
    return {
        "schema": "error_coupling_simulator.frontend.codespec_record_runner_summary.v1",
        "out_dir": str(ev.out_dir),
        "record_evidence": str(ev.record_evidence),
        "content_hash": ev.content_hash,
        "verdict": ev.manifest["verdict"],
        "passed": bool(ev.manifest["passed"]),
        "source_kind": ev.manifest["source_kind"],
        "source_hash": ev.manifest["source_hash"],
        "record_count": int(rec["record_count"]),
        "measurement_key_count": len(rec["measurement_keys"]),
        "applied_channel_count": int(rec["applied_channel_count"]),
        "measurement_basis": rec["measurement_basis"],
        "full_positive_duration_coverage": bool(cov["full_positive_duration_coverage"]),
        "freeze": (str(result.freeze.freeze_path) if result.freeze is not None else None),
    }


def test_L0_codespec_main_default_run_returns_zero(monkeypatch, capsys):
    """argv-not-None + validate_freeze None + freeze-present + passed True (return 0). Pins the CLI
    defaults threaded to run_* and the full printed summary against an independent recompute."""
    seen: dict = {}
    result = _fake_codespec_result(passed=True, with_freeze=True)

    def fake_run(out_dir, *, rounds, device, write_freeze, refresh_freeze):
        seen.update(out_dir=out_dir, rounds=rounds, device=device,
                    write_freeze=write_freeze, refresh_freeze=refresh_freeze)
        return result

    monkeypatch.setattr(cr, "run_axis1_codespec_record_fixture", fake_run)
    rc = cr.main([])
    assert rc == 0
    assert seen == {"out_dir": "outputs/simulator_validation/axis1_codespec_record_evidence",
                    "rounds": 2, "device": "cuda", "write_freeze": True, "refresh_freeze": False}
    assert capsys.readouterr().out == _dump(_expected_codespec_summary(result))


def test_L0_codespec_main_explicit_args_no_freeze_returns_one(monkeypatch, capsys):
    """--no-freeze (write_freeze False + freeze None arc) + passed False (return 1) + explicit args."""
    seen: dict = {}
    result = _fake_codespec_result(passed=False, with_freeze=False)

    def fake_run(out_dir, *, rounds, device, write_freeze, refresh_freeze):
        seen.update(out_dir=out_dir, rounds=rounds, device=device,
                    write_freeze=write_freeze, refresh_freeze=refresh_freeze)
        return result

    monkeypatch.setattr(cr, "run_axis1_codespec_record_fixture", fake_run)
    rc = cr.main(["--out-dir", "OUT", "--rounds", "3", "--device", "cpu",
                  "--no-freeze", "--refresh-freeze"])
    assert rc == 1
    assert seen == {"out_dir": "OUT", "rounds": 3, "device": "cpu",
                    "write_freeze": False, "refresh_freeze": True}
    expected = _expected_codespec_summary(result)
    assert expected["passed"] is False and expected["freeze"] is None   # freeze-None + passed-False arcs
    assert capsys.readouterr().out == _dump(expected)


def test_L0_codespec_main_validate_freeze_returns_zero(monkeypatch, capsys):
    """validate_freeze-not-None arc: validates + prints the validation dict + returns 0, never runs."""
    seen: dict = {}

    def fake_validate(path):
        seen["path"] = path
        return {"schema": "validation", "pass": True}

    def fail_run(*a, **k):  # must NOT be reached on the validate path
        raise AssertionError("run_* must not be called on the --validate-freeze path")

    monkeypatch.setattr(cr, "validate_axis1_measurement_record_freeze", fake_validate)
    monkeypatch.setattr(cr, "run_axis1_codespec_record_fixture", fail_run)
    rc = cr.main(["--validate-freeze", "some/records.freeze.json"])
    assert rc == 0
    assert seen["path"] == Path("some/records.freeze.json")
    assert capsys.readouterr().out == _dump({"schema": "validation", "pass": True})


def test_L0_codespec_main_argv_none_reads_sys_argv(monkeypatch):
    """parse_args(argv is None) arc: main() with argv=None reads sys.argv."""
    monkeypatch.setattr(sys, "argv", ["prog"])
    seen: dict = {}

    def fake_run(out_dir, **kw):
        seen.update(out_dir=out_dir, **kw)
        return _fake_codespec_result()

    monkeypatch.setattr(cr, "run_axis1_codespec_record_fixture", fake_run)
    assert cr.main() == 0
    assert seen["out_dir"] == "outputs/simulator_validation/axis1_codespec_record_evidence"


def test_L0_codespec_main_help_exact_strings(monkeypatch, capsys):
    """--help exposes every argparse option + its EXACT help string. Pinning the full (case-exact)
    help strings -- with COLUMNS wide so argparse never wraps them -- kills the help mutants
    (lower/UPPER case-swap, help=None, help dropped) that a loose substring/case check misses; an
    option-name mutant breaks parser construction. COLUMNS=300 keeps each ~73-char help contiguous."""
    monkeypatch.setenv("COLUMNS", "300")
    with pytest.raises(SystemExit):
        cr.main(["--help"])
    text = capsys.readouterr().out
    assert "XX" not in text
    for opt in ("--out-dir", "--rounds", "--device", "--no-freeze", "--refresh-freeze",
                "--validate-freeze"):
        assert opt in text
    for h in (
        "Directory for axis1_measurement_records.json and optional freeze manifest.",
        "CodeSpec measurement rounds.",
        "Torch device. The release lane is cuda.",
        "Write axis1_measurement_records.json without a freeze manifest.",
        "Overwrite the record freeze after an intentional evidence update.",
        "Validate an existing record freeze manifest instead of generating evidence.",
    ):
        assert h in text


# =========================================================================== #
# joint_channel_comparison_runner: build_joint_channel_comparison_schedule                                  #
# =========================================================================== #
def test_L0_build_joint_channel_schedule():
    sch = gr.build_joint_channel_comparison_schedule()
    assert isinstance(sch, SubstepSchedule)
    assert sch.num_qubits == 2
    assert sch.source_kind == "circuit_ir"
    assert has_valid_compiler_schedule_seal(sch) is True
    assert all(su.generated_by_compiler for su in sch.substeps)
    assert sch.static_zz_couplings == ((0, 1),)
    # the declared H(0), tick, CZ(0,1) lower to exactly these three ordered substeps.
    assert [su.kind for su in sch.substeps] == ["one_qubit_gate", "barrier", "two_qubit_gate"]
    assert [[(op.name, tuple(op.targets)) for op in su.operations] for su in sch.substeps] == [
        [("H", (0,))], [], [("CZ", (0, 1))],
    ]
    # deterministic sha256 identity: catches metadata / num_qubits / edge / gate-target mutations.
    assert sch.source_hash == _JOINT_CHANNEL_SOURCE_HASH


def test_L1_joint_channel_schedule_is_valid_and_sealed():
    """FAITHFULNESS: sealed compiler schedule with sequential order_index and in-range windows."""
    sch = gr.build_joint_channel_comparison_schedule()
    for i, su in enumerate(sch.substeps):
        assert su.order_index == i
        assert all(0 <= q < sch.num_qubits for q in su.window_support)


def test_DISCRIMINATES_joint_channel_hash_pin_bites_wrong_qubit_count():
    """The joint-channel source_hash pin has teeth: HOLDS for the fixture, FAILS for any schedule with a
    different qubit count (an independent 3q build)."""
    from error_coupling_simulator.frontend.circuit_ir import CircuitBuilder
    from error_coupling_simulator.frontend.analog_schedule import circuit_ir_to_substep_schedule

    def other():
        b = CircuitBuilder(num_qubits=3, metadata={"fixture": "joint_channel_comparison",
                                                   "encoded_distance_certified": False})
        b.declare_static_zz_couplings(((0, 1),))
        b.h(0)
        b.tick()
        b.cz((0, 1))
        return circuit_ir_to_substep_schedule(b.build())

    def prop(sch):
        assert sch.source_hash == _JOINT_CHANNEL_SOURCE_HASH
    assert_discriminates(prop, gr.build_joint_channel_comparison_schedule(), other(), label="joint_channel_hash")


# =========================================================================== #
# joint_channel_comparison_runner: run_joint_channel_comparison_fixture (GPU callee monkeypatched)          #
# =========================================================================== #
def _patch_joint_channel_writers(monkeypatch):
    calls: dict = {}
    fake_ev = _fake_joint_channel_evidence()
    fake_frz = SimpleNamespace(freeze_path=Path("fake/comparison/dir/joint_channel_comparison.freeze.json"))

    def fake_write(schedule, out_dir, *, device="cuda"):
        calls["write"] = {"schedule": schedule, "out_dir": out_dir, "device": device}
        return fake_ev

    def fake_freeze(joint_channel_comparison, *, overwrite=False):
        calls["freeze"] = {"joint_channel_comparison": joint_channel_comparison, "overwrite": overwrite}
        return fake_frz

    monkeypatch.setattr(gr, "write_joint_channel_comparison_evidence", fake_write)
    monkeypatch.setattr(gr, "freeze_joint_channel_comparison_evidence", fake_freeze)
    return calls, fake_ev, fake_frz


def test_L0_run_joint_channel_fixture_defaults_freeze_on(monkeypatch):
    calls, fake_ev, fake_frz = _patch_joint_channel_writers(monkeypatch)
    res = gr.run_joint_channel_comparison_fixture("comparison/out")
    assert isinstance(res.schedule, SubstepSchedule) and res.schedule.num_qubits == 2
    assert res.schedule.source_hash == _JOINT_CHANNEL_SOURCE_HASH
    assert calls["write"]["schedule"] is res.schedule
    assert calls["write"]["out_dir"] == "comparison/out"
    assert calls["write"]["device"] == "cuda"
    assert calls["freeze"]["joint_channel_comparison"] == fake_ev.joint_channel_comparison
    assert calls["freeze"]["overwrite"] is False
    assert res.evidence is fake_ev
    assert res.freeze is fake_frz


def test_L0_run_joint_channel_fixture_explicit_args_freeze_off(monkeypatch):
    calls, _, _ = _patch_joint_channel_writers(monkeypatch)
    res = gr.run_joint_channel_comparison_fixture("gg", device="cpu", write_freeze=False, refresh_freeze=True)
    assert calls["write"]["out_dir"] == "gg"
    assert calls["write"]["device"] == "cpu"
    assert "freeze" not in calls
    assert res.freeze is None


def test_L0_run_joint_channel_fixture_threads_refresh_freeze(monkeypatch):
    calls, _, _ = _patch_joint_channel_writers(monkeypatch)
    gr.run_joint_channel_comparison_fixture("gg", refresh_freeze=True)
    assert calls["freeze"]["overwrite"] is True


# =========================================================================== #
# joint_channel_comparison_runner: main                                                              #
# =========================================================================== #
def _expected_joint_channel_summary(result: SimpleNamespace) -> dict:
    ev = result.evidence
    return {
        "schema": "error_coupling_simulator.frontend.joint_channel_comparison_runner_summary.v1",
        "out_dir": str(ev.out_dir),
        "joint_channel_comparison": str(ev.joint_channel_comparison),
        "content_hash": ev.content_hash,
        "verdict": ev.manifest["verdict"],
        "passed": bool(ev.manifest["passed"]),
        "row_count": len(ev.manifest["rows"]),
        "freeze": (str(result.freeze.freeze_path) if result.freeze is not None else None),
    }


def test_L0_joint_channel_main_default_run_returns_zero(monkeypatch, capsys):
    seen: dict = {}
    result = _fake_joint_channel_result(passed=True, with_freeze=True)

    def fake_run(out_dir, *, device, write_freeze, refresh_freeze):
        seen.update(out_dir=out_dir, device=device, write_freeze=write_freeze,
                    refresh_freeze=refresh_freeze)
        return result

    monkeypatch.setattr(gr, "run_joint_channel_comparison_fixture", fake_run)
    rc = gr.main([])
    assert rc == 0
    assert seen == {"out_dir": "outputs/simulator_validation/joint_channel_comparison",
                    "device": "cuda", "write_freeze": True, "refresh_freeze": False}
    assert capsys.readouterr().out == _dump(_expected_joint_channel_summary(result))


def test_L0_joint_channel_main_explicit_args_no_freeze_returns_one(monkeypatch, capsys):
    seen: dict = {}
    result = _fake_joint_channel_result(passed=False, with_freeze=False)

    def fake_run(out_dir, *, device, write_freeze, refresh_freeze):
        seen.update(out_dir=out_dir, device=device, write_freeze=write_freeze,
                    refresh_freeze=refresh_freeze)
        return result

    monkeypatch.setattr(gr, "run_joint_channel_comparison_fixture", fake_run)
    rc = gr.main(["--out-dir", "GG", "--device", "cpu", "--no-freeze", "--refresh-freeze"])
    assert rc == 1
    assert seen == {"out_dir": "GG", "device": "cpu", "write_freeze": False, "refresh_freeze": True}
    expected = _expected_joint_channel_summary(result)
    assert expected["passed"] is False and expected["freeze"] is None   # freeze-None + passed-False arcs
    assert capsys.readouterr().out == _dump(expected)


def test_L0_joint_channel_main_validate_freeze_returns_zero(monkeypatch, capsys):
    seen: dict = {}

    def fake_validate(path):
        seen["path"] = path
        return {"schema": "joint_channel_validation", "pass": True}

    def fail_run(*a, **k):
        raise AssertionError("run_* must not be called on the --validate-freeze path")

    monkeypatch.setattr(gr, "validate_joint_channel_comparison_freeze", fake_validate)
    monkeypatch.setattr(gr, "run_joint_channel_comparison_fixture", fail_run)
    rc = gr.main(["--validate-freeze", "some/joint_channel_comparison.freeze.json"])
    assert rc == 0
    assert seen["path"] == Path("some/joint_channel_comparison.freeze.json")
    assert capsys.readouterr().out == _dump({"schema": "joint_channel_validation", "pass": True})


def test_L0_joint_channel_main_argv_none_reads_sys_argv(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog"])
    seen: dict = {}

    def fake_run(out_dir, **kw):
        seen.update(out_dir=out_dir, **kw)
        return _fake_joint_channel_result()

    monkeypatch.setattr(gr, "run_joint_channel_comparison_fixture", fake_run)
    assert gr.main() == 0
    assert seen["out_dir"] == "outputs/simulator_validation/joint_channel_comparison"


def test_L0_joint_channel_main_help_exact_strings(monkeypatch, capsys):
    monkeypatch.setenv("COLUMNS", "300")
    with pytest.raises(SystemExit):
        gr.main(["--help"])
    text = capsys.readouterr().out
    assert "XX" not in text
    for opt in ("--out-dir", "--device", "--no-freeze", "--refresh-freeze", "--validate-freeze"):
        assert opt in text
    for h in (
        "Directory for joint_channel_comparison.json and optional freeze manifest.",
        "Torch device. The release lane is cuda.",
        "Write comparison evidence without its freeze manifest.",
        "Overwrite the freeze manifest after an intentional evidence update.",
        "Validate an existing freeze manifest instead of generating evidence.",
    ):
        assert h in text


# =========================================================================== #
# module __all__ pins (public-surface mutants)                                 #
# =========================================================================== #
def test_public_api_all_pinned():
    assert set(cr.__all__) == {
        "Axis1CodeSpecRecordRunnerResult",
        "build_axis1_codespec_4q_frontend_spec",
        "build_axis1_codespec_frontend_schedule",
        "build_axis1_codespec_frontend_spec",
        "main",
        "run_axis1_codespec_record_fixture",
    }
    assert set(gr.__all__) == {
        "JointChannelComparisonRunnerResult",
        "build_joint_channel_comparison_schedule",
        "main",
        "run_joint_channel_comparison_fixture",
    }
