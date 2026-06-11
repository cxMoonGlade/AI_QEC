"""ADR 0008 SEAM-TEST — registered pin/verdict logic tests (synthetic inputs ONLY).

Covers builder S3's slice of the frozen pre-registration
(docs/metric_results.md "ADR 0008 SEAM-TEST PRE-REGISTRATION"): the K1 falsifier
verdict state machine (item 10) with its precedence rule, the P-c phi-scaling
classifier (item 4), the no-fit R_det/T3 scorers on the analytic T-B law (item 6,
D5), STRUCTURAL/EMERGENT pin routing (item 7), the registered stage-order
enforcement incl. the W2-before-any-fit abort (item 11), the reviewer gate
(--reviewed refusal), and the claim-language template (items 12/39: controlled-
teacher-scoped; hardware-claim wording structurally absent).

FIX ROUND 2 (build_R2_seam_postfix_review.md): also covers the AMENDMENT-2
P-a routing split (rulings 11-13: (a) pin = rounds=1/repeats=1 + the
stochastic-backdrop control; multi-round rows -> the REPORTED visibility table
under the 1e-1 (c) tripwire — R2-2), the record-level branch-aligned oracle
KL/TV adaptors (R2-3), the item-14 floor clause on the well-specified
tb_bunching arm (R2-4/E-3), the PSD score-Fisher gate spectra (R2-5/E-4),
the oracle-row-scoped compute envelope (E-6), and the section-E (c)-constant
declarations.

NO production compute: every input here is synthetic, closed-form, or a
(2,2)-toy carrier law (the adaptor PSD-spectrum check — same scale as the S2
suite's own toys; torch enters the test path only for those adaptor checks).
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "outputs" / "seam_test_report.py"
_spec = importlib.util.spec_from_file_location("seam_test_report", _MODULE_PATH)
mod = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("seam_test_report", mod)
_spec.loader.exec_module(mod)

_ADAPTOR_PATH = Path(__file__).resolve().parents[1] / "outputs" / "seam_test_adaptors.py"


def _adaptors():
    """Load the S3 adaptor module (the orchestrator's own loader pattern)."""
    name = "seam_test_adaptors"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, _ADAPTOR_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------- #
# synthetic measurement bundles                                                #
# --------------------------------------------------------------------------- #
def _measurements(
    *,
    residual_scale: float,
    banded: bool,
    structural_failures: tuple[str, ...] = (),
    contamination: bool = False,
    floor: float = 1e-12,
) -> "mod.SeamMeasurements":
    phis = mod.PHI_GRID
    residual = {
        "sandwich": {p: residual_scale * p**2 for p in phis},
        "k2ry": {p: residual_scale * p for p in phis},
    }
    band = None
    derivation = None
    if banded:
        band = {fn: {p: 2.0 * abs(v) + 1e-6 for p, v in per.items()} for fn, per in residual.items()}
        derivation = "synthetic derived band (test stand-in for the functional-indexed derivation)"
    return mod.SeamMeasurements(
        phi_grid=phis,
        residual_by_phi=residual,
        residual_floor=floor,
        band_by_phi=band,
        band_derivation=derivation,
        structural_pin_failures=structural_failures,
        in_window_contamination=contamination,
    )


# --------------------------------------------------------------------------- #
# item 10 — K1 verdict state machine: each branch driven exactly once          #
# --------------------------------------------------------------------------- #
def test_k1_verdict_establish_band():
    verdict = mod.k1_verdict(_measurements(residual_scale=1e-3, banded=True))
    assert verdict["verdict"] == mod.VERDICT_ESTABLISH_BAND
    assert verdict["triggers_c3_module"] is True
    assert verdict["k1_discharged"] is True
    assert "discharged-by-band" in verdict["registered_semantics"]
    assert verdict["epistemic_class"] == "c"  # decision rule: go/no-go gating only


def test_k1_verdict_abstain():
    verdict = mod.k1_verdict(_measurements(residual_scale=1e-3, banded=False))
    assert verdict["verdict"] == mod.VERDICT_ABSTAIN
    assert verdict["triggers_c3_module"] is False
    assert verdict["k1_discharged"] is False
    assert "window-limited fallback" in verdict["registered_semantics"]


def test_k1_verdict_kill_precedence():
    # PRECEDENCE: residual at floor would be NULL, but a structural-pin break
    # forces KILL-C1 regardless of residual (registered item 10).
    verdict = mod.k1_verdict(
        _measurements(residual_scale=0.0, banded=True, structural_failures=("unital_pin",))
    )
    assert verdict["verdict"] == mod.VERDICT_KILL_C1
    assert verdict["residual_at_floor"] is True  # the overridden branch, echoed
    assert verdict["k1_discharged"] is False
    assert "ADR 0008 fallback" in verdict["registered_semantics"]
    # IN-WINDOW contamination alone also kills (the other registered KILL trigger).
    contaminated = mod.k1_verdict(
        _measurements(residual_scale=1e-3, banded=True, contamination=True)
    )
    assert contaminated["verdict"] == mod.VERDICT_KILL_C1


def test_k1_verdict_null():
    # residual at floor + ALL pins green => NULL (K1 trivially discharged,
    # regime scope carried; the C3 module is NOT triggered).
    verdict = mod.k1_verdict(_measurements(residual_scale=0.0, banded=False))
    assert verdict["verdict"] == mod.VERDICT_NULL
    assert verdict["triggers_c3_module"] is False
    assert verdict["k1_discharged"] is True
    assert "regime scope carried" in verdict["registered_semantics"]


def test_k1_verdict_outputs_complete():
    # every branch returns the registered claim paragraph + a compute-ledger row
    for kwargs in (
        {"residual_scale": 1e-3, "banded": True},
        {"residual_scale": 1e-3, "banded": False},
        {"residual_scale": 0.0, "banded": False},
        {"residual_scale": 0.0, "banded": True, "structural_failures": ("unital_pin",)},
    ):
        verdict = mod.k1_verdict(_measurements(**kwargs))
        assert verdict["claim_paragraph"]
        row = verdict["compute_ledger_row"]
        assert row["stage"] == "k1_verdict" and row["n_fits"] == 0


# --------------------------------------------------------------------------- #
# item 4 (P-c) — phi-scaling classifier on the registered regime grid          #
# --------------------------------------------------------------------------- #
def test_phi_scaling_classifier_quadratic_linear_flat_floor():
    phis = mod.PHI_GRID
    assert phis[0] == mod.PHI_REGIME[0] and phis[-1] == mod.PHI_REGIME[1]
    quad = mod.classify_phi_scaling(phis, [0.3 * p**2 for p in phis])
    assert quad["classification"] == "quadratic"
    assert abs(quad["slope"] - 2.0) < 1e-9  # exact synthetic power law
    lin = mod.classify_phi_scaling(phis, [0.3 * p for p in phis])
    assert lin["classification"] == "linear"
    assert abs(lin["slope"] - 1.0) < 1e-9
    flat = mod.classify_phi_scaling(phis, [1e-3 for _ in phis])
    assert flat["classification"] == "flat"
    floor = mod.classify_phi_scaling(phis, [1e-14 for _ in phis], floor=1e-12)
    assert floor["classification"] == "floor" and floor["slope"] is None
    # registered P-c expectations carried as data
    assert mod.PC_EXPECTED_SCALING == {"sandwich": "quadratic", "k2ry": "linear"}


def test_phi_scaling_classifier_rejects_degenerate_input():
    with pytest.raises(ValueError):
        mod.classify_phi_scaling([0.1], [1e-3])
    with pytest.raises(ValueError):
        mod.classify_phi_scaling([0.1, 0.1], [1e-3, 2e-3])


# --------------------------------------------------------------------------- #
# item 6 — R_det scorer on the analytic T-B law (registered D5 member)          #
# --------------------------------------------------------------------------- #
def test_r_det_scorer_on_analytic_tb_law():
    p01, p10 = mod.TB_MEMBER_P01, mod.TB_MEMBER_P10
    member = mod.tb_member(p01, p10)
    # registered member identities: r = 1.27e-2, R = 5, lambda1 = 0.873 (D5 (a))
    assert abs(member["r"] - mod.TB_MEMBER_r) / mod.TB_MEMBER_r < 1e-4
    assert abs(member["R"] - mod.TB_MEMBER_R) < 1e-3
    assert abs(member["lambda1"] - mod.TB_MEMBER_LAMBDA1) < 1e-6
    assert abs(member["lambda1"] - (1.0 - 2.0 * member["r"] * member["R"])) < 1e-12

    # exact two-block marginals of the record chain -> scorer -> R_k matches the
    # T-B law R_k = 1 + (R-1) lambda1^(k-1) (no fit anywhere)
    joint = {k: mod.tb_lag_joint(p01, p10, k) for k in range(1, 7)}
    scored = mod.score_r_det(joint, member["r"])
    for k in range(1, 7):
        predicted = 1.0 + (member["R"] - 1.0) * member["lambda1"] ** (k - 1)
        assert abs(scored[k]["R_k"] - predicted) < 1e-9 * predicted
        assert abs(mod.predict_r_k(member["r"], member["R"], k) - predicted) < 1e-9
    # lag-1 consistency: R_1 = R exactly (P(FF) = p01*p10)
    assert abs(scored[1]["R_k"] - member["R"]) < 1e-9 * member["R"]

    # attribution lags k >= 2 ONLY (D5 readout-contamination design rule)
    assert scored[1]["attribution_legal"] is False
    assert all(scored[k]["attribution_legal"] for k in range(2, 7))
    assert mod.attribution_lags(scored) == [2, 3, 4, 5, 6]
    # record convention declared on every row (D5<->K2 convention pin)
    assert all("data-record-chain" in scored[k]["record"] for k in scored)


def test_t3_triple_pin_tb_exact():
    p01, p10 = mod.TB_MEMBER_P01, mod.TB_MEMBER_P10
    member = mod.tb_member(p01, p10)
    t3 = mod.t3_statistic(mod.tb_triple_joint(p01, p10), member["r"])
    # T-B predicts T3 = R EXACTLY (renewal after two flips)
    assert abs(t3 - member["R"]) < 1e-9 * member["R"]
    assert mod.tb_t3_prediction(member["R"]) == member["R"]
    # the Skew_pi(f) >= 0 restriction is carried with the pin (D5 T3 overreach fix)
    assert "Skew" in mod.T3_SKEW_RESTRICTION
    # cross-check on a second member (R = 2 row of the D5 table)
    m2 = mod.tb_member(7.4395e-3, 4.33605e-2)
    assert abs(m2["R"] - 2.0) < 1e-3
    t3_2 = mod.t3_statistic(mod.tb_triple_joint(7.4395e-3, 4.33605e-2), m2["r"])
    assert abs(t3_2 - m2["R"]) < 1e-9 * m2["R"]


def test_r_det_scorer_input_validation():
    with pytest.raises(ValueError):
        mod.score_r_det({2: 1e-4}, 0.0)
    with pytest.raises(ValueError):
        mod.predict_r_k(1e-2, 5.0, 0)
    with pytest.raises(ValueError):
        mod.tb_lag_joint(1e-2, 1e-1, 0)


# --------------------------------------------------------------------------- #
# item 7 — STRUCTURAL vs EMERGENT routing                                      #
# --------------------------------------------------------------------------- #
def test_structural_violation_halts():
    results = [
        mod.PinResult(mod.pin_spec("unital_pin"), measured=3e-4, passed=False, arm="backdrop"),
        mod.PinResult(mod.pin_spec("fixed_point_trace_norm"), measured=1e-12, passed=True),
    ]
    routing = mod.route_pin_results(results)
    assert routing["halt"] is True
    assert [bug["pin"] for bug in routing["build_bugs"]] == ["unital_pin"]
    assert routing["build_bugs"][0]["label"] == mod.STRUCTURAL
    assert "BUILD BUG" in routing["build_bugs"][0]["disposition"]
    assert routing["findings"] == [] and routing["signals"] == []


def test_emergent_violation_is_a_finding_not_a_halt():
    results = [
        mod.PinResult(mod.pin_spec("q_eff_flatness"), measured=2.5, passed=False, arm="backdrop"),
        mod.PinResult(mod.pin_spec("h2_t1_blindness_across_seam"), measured=1e-6, passed=False,
                      arm="seam_teacher"),
    ]
    routing = mod.route_pin_results(results)
    assert routing["halt"] is False
    assert {f["pin"] for f in routing["findings"]} == {
        "q_eff_flatness", "h2_t1_blindness_across_seam"
    }
    assert all("FINDING" in f["disposition"] for f in routing["findings"])
    assert routing["build_bugs"] == []


def test_d2_long_range_violation_under_seam_teacher_is_the_signal():
    results = [
        mod.PinResult(mod.pin_spec("d2_long_range_null"), measured=4e-3, passed=False,
                      arm="seam_teacher_phi_0.1"),
    ]
    routing = mod.route_pin_results(results)
    assert routing["halt"] is False
    assert routing["build_bugs"] == [] and routing["findings"] == []
    assert len(routing["signals"]) == 1
    assert "SIGNAL" in routing["signals"][0]["disposition"]


def test_all_registered_pins_carry_labels_and_classes():
    for pin in mod.THEOREM_PINS:
        assert pin.label in (mod.STRUCTURAL, mod.EMERGENT)
        assert pin.epistemic_class in ("a", "b", "c")
    # the registered split (spot checks against the frozen item 7 text)
    assert mod.pin_spec("h2_t1_blindness_in_window").label == mod.STRUCTURAL
    assert mod.pin_spec("h2_t1_blindness_across_seam").label == mod.EMERGENT
    assert mod.pin_spec("t_a_pauli_ablation_R1").label == mod.STRUCTURAL
    assert mod.pin_spec("fixed_point_trace_norm").threshold == 1e-9
    assert mod.pin_spec("zero_nonpositive_probability").threshold == 0.0
    assert mod.pin_spec("d2_long_range_null").violation_is_signal is True


# --------------------------------------------------------------------------- #
# item 11 — stage order: the fit stage refuses before the W2 gate stage        #
# --------------------------------------------------------------------------- #
def test_stage_order_fit_refuses_before_w2_gate():
    ledger = mod.StageLedger()
    with pytest.raises(mod.StageOrderError):
        ledger.start("carrier_fits")
    ledger.start("provenance")
    ledger.complete("provenance", {})
    with pytest.raises(mod.StageOrderError):
        ledger.start("carrier_fits")  # W2 gate still missing
    ledger.start("w2_gate")
    ledger.complete("w2_gate", {}, passed=True)
    with pytest.raises(mod.StageOrderError):
        ledger.start("carrier_fits")  # P-a/P-b still missing (strict registered order)
    ledger.start("pa_pb_structural")
    ledger.complete("pa_pb_structural", {})
    ledger.start("carrier_fits")  # now legal


def test_w2_gate_failure_aborts_before_any_fit():
    ledger = mod.StageLedger()
    ledger.start("provenance")
    ledger.complete("provenance", {})
    ledger.start("w2_gate")
    ledger.complete("w2_gate", {"reason": "edge DOF invisible"}, passed=False)
    with pytest.raises(mod.GateAbortError):
        ledger.start("carrier_fits")
    with pytest.raises(mod.GateAbortError):
        ledger.start("pa_pb_structural")  # abort is total: nothing after the gate runs
    with pytest.raises(mod.GateAbortError):
        ledger.start("k1_verdict")


def test_structural_halt_permits_only_the_verdict():
    ledger = mod.StageLedger()
    for stage in ("provenance", "w2_gate", "pa_pb_structural", "carrier_fits"):
        ledger.start(stage)
        ledger.complete(stage, {})
    ledger.halt("unital_pin broke (STRUCTURAL)")
    with pytest.raises(mod.StageOrderError):
        ledger.start("pc_seam_residual")  # measurement stages frozen
    ledger.start("k1_verdict")  # the forced KILL-C1 verdict may still render


def test_stage_ledger_rejects_unknown_stage():
    ledger = mod.StageLedger()
    with pytest.raises(ValueError):
        ledger.start("not_a_stage")
    with pytest.raises(ValueError):
        ledger.complete("not_a_stage", {})


# --------------------------------------------------------------------------- #
# items 12 + 39 — claim language: controlled-teacher scope, no hardware claims #
# --------------------------------------------------------------------------- #
def test_claim_language_scope_and_forbidden_phrases():
    # local copy of hard forbidden phrases (independent of the module's own list)
    locally_forbidden = (
        "fits the device",
        "do() on hardware",
        "hardware counterfactual",
        "this residual is leakage",
        "is leakage",
        "validated on hardware",
        "hardware edge-coherence established",
    )
    for verdict_key in mod.K1_VERDICT_SEMANTICS:
        paragraph = mod.claim_language(verdict_key)
        lowered = paragraph.lower()
        for phrase in mod.REQUIRED_SCOPE_PHRASES:
            assert phrase.lower() in lowered, f"missing scope phrase {phrase!r} for {verdict_key}"
        for phrase in mod.FORBIDDEN_CLAIM_PHRASES + locally_forbidden:
            assert phrase.lower() not in lowered, (
                f"claim language for {verdict_key} emits forbidden phrase {phrase!r}"
            )
        # the registered semantics are embedded, controlled-teacher scope explicit
        assert verdict_key in paragraph
        assert str(mod.PHI_REGIME[0]) in paragraph and str(mod.PHI_REGIME[1]) in paragraph
    with pytest.raises(KeyError):
        mod.claim_language("NOT-A-VERDICT")


def test_item39_verbatim_text_is_data_not_emitted():
    # the ADR 0007 verbatim forbidden-claims text is carried as DATA (item 39)
    assert "fits the device" in mod.R2_LITE_FORBIDDEN_CLAIMS_VERBATIM
    # ... and is NOT interpolated into any emitted claim paragraph
    for verdict_key in mod.K1_VERDICT_SEMANTICS:
        assert mod.R2_LITE_FORBIDDEN_CLAIMS_VERBATIM not in mod.claim_language(verdict_key)


# --------------------------------------------------------------------------- #
# reviewer gate + registration data integrity                                  #
# --------------------------------------------------------------------------- #
def test_main_refuses_without_reviewed_flag(tmp_path, capsys):
    state_dir = tmp_path / "seam_run"
    rc = mod.main(["--state-dir", str(state_dir)])
    assert rc == 2
    assert not state_dir.exists()  # refusal creates NO state and runs NO stage
    out = capsys.readouterr().out
    assert "NOT RUN" in out and "--reviewed" in out


def test_registration_constants_and_classes():
    assert mod.PHI_REF == 0.1
    assert mod.PHI_REGIME == (0.05, 0.15)
    assert mod.ATTRIBUTION_MIN_LAG == 2
    for item, row in mod.REGISTRATION_CLASS_TABLE.items():
        assert row["class"] in ("a", "b", "c"), item
    assert mod.epistemic_class("P-c") == "b"          # THE K1 measurement
    assert mod.epistemic_class("P-a") == "a"
    assert mod.epistemic_class("k1_verdict_rule") == "c"
    assert mod.epistemic_class("undeclared-item") == "c"  # METRICS.md default
    # G-NLL disposition rows: registered items 2/3/9/16/17 are N/A-with-reason
    na_items = {row["item"] for row in mod.GNLL_DISPOSITION if row["disposition"] == "N/A"}
    assert na_items == {"checklist-2", "checklist-3", "checklist-9", "checklist-16", "checklist-17"}
    assert all(row["detail"] for row in mod.GNLL_DISPOSITION)
    live = {row["item"] for row in mod.GNLL_DISPOSITION if row["disposition"] == "LIVE"}
    assert live == {"G-NLL(i)", "G-NLL(iv)"}
    floors = {row["item"] for row in mod.GNLL_DISPOSITION if row["disposition"] == "FLOOR-PIN"}
    assert floors == {"G-NLL(ii)", "G-NLL(iii)"}
    # determinism items 14 + 15 carried verbatim
    assert "gradcheck <=1e-10" in mod.CHECKLIST_ITEM_14_VERBATIM
    assert "P1h verbatim" in mod.CHECKLIST_ITEM_15_VERBATIM
    assert "never silent widening" in mod.CHECKLIST_ITEM_15_VERBATIM


def test_compute_envelope_check():
    rows = [
        mod.compute_ledger_row("carrier_fits", device="cuda", n_fits=150,
                               wall_clock_s=150 * 20.0, peak_mem_gb=8.0),
    ]
    # E-6: a FIT row may legitimately peak at several GB — the 1.1 GB item-13
    # envelope is scored on oracle_row rows ONLY; the all-rows peak is reported.
    verdict = mod.check_compute_envelope(rows)
    assert verdict["within_envelope"] is True
    assert verdict["peak_mem_gb_all_rows"] == 8.0
    assert verdict["peak_mem_gb_oracle_rows"] == 0.0
    rows.append(mod.compute_ledger_row("pa_pb_structural", device="cuda", n_fits=0,
                                       wall_clock_s=10.0, peak_mem_gb=2.0,
                                       oracle_row=True))
    rows.append(mod.compute_ledger_row("carrier_fits", device="cuda", n_fits=100,
                                       wall_clock_s=50000.0, peak_mem_gb=0.5))
    verdict = mod.check_compute_envelope(rows)
    assert verdict["within_envelope"] is False
    assert len(verdict["violations"]) == 3  # fits > 200, wall > half-day, oracle mem > 1.1 GB
    assert any("oracle" in v for v in verdict["violations"])
    assert verdict["peak_mem_gb_oracle_rows"] == 2.0


def test_provenance_manifest_voids_undeclared_inputs():
    manifest = mod.build_provenance_manifest(mod.DECLARED_LEARNER_INPUTS)
    assert manifest["voids_fit_on_undeclared"] is True
    assert len(manifest["rows"]) == len(mod.DECLARED_LEARNER_INPUTS)
    with pytest.raises(ValueError):
        mod.build_provenance_manifest([{"name": "mystery blob", "role": "fitting", "provenance": ""}])
    # legality table carries the registered prohibitions
    illegal = {row["input"] for row in mod.LEGALITY_TABLE if not row["legal"]}
    assert "hardware data (any Google release)" in illegal
    assert "held-out-split statistics" in illegal
    assert "teacher channels / parameters / labels" in illegal


def test_determinism_scorer_items_14_15():
    good = {
        "gradcheck_max_error": 5e-11,
        "closure_calls_bit_equal": True,
        "fisher_rank_matches_exact": True,
        "fit_converged_seed_robust": True,
        "graph_law_bit_exact": True,
        "lbfgs_trajectory_bit_exact": True,
    }
    assert mod.score_determinism(good)["passed"] is True
    # disclosed re-association path: legal iff gradients <= 1e-12 relative
    reassoc = dict(good, graph_law_bit_exact=False, reassociation_disclosed=True,
                   reassociation_grad_rel_error=5e-13)
    assert mod.score_determinism(reassoc)["passed"] is True
    bad_reassoc = dict(reassoc, reassociation_grad_rel_error=1e-9)
    assert mod.score_determinism(bad_reassoc)["passed"] is False
    # silent widening forbidden: trajectory not bit-exact and NO registered downgrade
    silent = dict(good, lbfgs_trajectory_bit_exact=False)
    assert mod.score_determinism(silent)["passed"] is False
    declared = dict(silent, registered_tolerance_downgrade="tolerance 1e-14, registered")
    assert mod.score_determinism(declared)["passed"] is True
    # item 14 gradcheck floor enforced
    bad_grad = dict(good, gradcheck_max_error=1e-9)
    assert mod.score_determinism(bad_grad)["passed"] is False


def test_eigen_split_stability_item_32():
    assert mod.eigen_split_stable([1.0, 0.5, 1e-9], [0.9, 0.6, 1e-10]) is True
    # null mass GROWING under refinement => manufactured Fisher info => unstable
    assert mod.eigen_split_stable([1.0, 0.5, 1e-9], [0.9, 0.6, 1e-5]) is False
    # well-count change => unstable
    assert mod.eigen_split_stable([1.0, 0.5, 1e-9], [0.9, 1e-9, 1e-10]) is False


def test_render_report_ends_with_audit_skeleton():
    state = {"k1_verdict": mod.k1_verdict(_measurements(residual_scale=0.0, banded=False))}
    report = mod.render_report(state)
    assert "Metric audit" in report and "Rigor audit" in report
    assert report.index("Metric audit") < report.index("Rigor audit")
    assert "controlled-teacher-scoped" in report
    # epistemic discipline echoed in the skeleton
    assert "theorem-backed vs PROVISIONAL" in report


# --------------------------------------------------------------------------- #
# FIX-ROUND wiring tests (orchestrator, 2026-06-10, post-AMENDMENT 1+2):        #
# the reviewer change-list items wired by the S3 fix round, unit-tested here    #
# (mirrors the post-amendment RECONCILE probes of the integration gate).        #
# --------------------------------------------------------------------------- #
def test_score_pb_ruling_9_encoding():
    # AMENDMENT ruling 9: sign theorem-zero AND sin^2(phi) rate visible
    good = mod.score_pb(sign_gap=1e-13, rate_gap=1e-3)
    assert good["passed"] and good["twirl_sign_theorem_zero"] and good["sin2_rate_visible"]
    assert "retired" in good["encoding"]  # the quiet-law-gap-zero encoding is gone
    # rate invisible => FAIL (the old encoding would have called this a pass)
    assert not mod.score_pb(sign_gap=1e-13, rate_gap=0.0)["passed"]
    # sign gap above numerical zero => FAIL (theorem violation)
    assert not mod.score_pb(sign_gap=1e-6, rate_gap=1e-3)["passed"]


def test_score_in_window_contamination_ruling_6():
    lo = mod.score_in_window_contamination(5e-4)
    hi = mod.score_in_window_contamination(2e-3)
    assert lo["trigger"] is False and hi["trigger"] is True
    assert abs(lo["trigger_threshold"] - 1e-3) < 1e-15
    assert lo["epistemic_class"] == "c"  # gating only, never a premise


def test_score_r_det_from_rk_no_double_normalization():
    # synthetic S2 r_det_lag-shaped rows: R_k echoed verbatim, never re-divided
    rows = {
        1: {"R_k": 5.0, "p_joint": 8.06e-4, "flip_rate": 1.27e-2, "record": "data-record-chain"},
        2: {"R_k": 4.492, "p_joint": 7.245e-4, "flip_rate": 1.27e-2, "record": "data-record-chain"},
        3: {"R_k": 4.048, "p_joint": 6.529e-4, "flip_rate": 1.27e-2, "record": "data-record-chain"},
    }
    scored = mod.score_r_det_from_rk(rows)
    for k, row in rows.items():
        assert scored[k]["R_k"] == row["R_k"]  # verbatim -- no re-normalization
    assert mod.attribution_lags(scored) == [2, 3]  # k >= 2 only (registered)
    assert "data-record-chain" in scored[2]["record"]


def test_registered_pin_name_mapping():
    # S2 module pin callables map onto registered THEOREM_PINS entries
    for s2_name in ("normalization_pin", "nonpositive_pin", "fixed_point_pin",
                    "pauli_ablation_pin", "zero_seam_exactness_pin"):
        spec = mod.registered_pin_for(s2_name)
        assert spec is not None, s2_name
    # an unmapped pin name is a class-manifest violation (registered semantics)
    with pytest.raises(mod.StructuralPinViolation):
        mod.registered_pin_for("not_a_registered_pin")


# --------------------------------------------------------------------------- #
# FIX ROUND 2 (R2-2..R2-5 + section-E declarations, 2026-06-10):                #
# the second-round re-review items, unit-tested on synthetic/toy inputs.        #
# --------------------------------------------------------------------------- #
def test_pa_row_routing_amendment2_ruling_11():
    # R2-2 / ruling 11: the (a) pin = rounds=1 AND repeats=1 rows only...
    assert mod.pa_row_route(1, 1) == "a-pin"
    # ...multi-round repeats=1 rows -> the ruling-12 REPORTED visibility table
    assert mod.pa_row_route(2, 1) == "visibility"
    assert mod.pa_row_route(4, 1) == "visibility"
    # ...and the stochastic-backdrop control is an (a) row at ANY round count
    assert mod.pa_row_route(4, 1, stochastic_backdrop=True) == "a-pin"
    # repeats >= 2 contexts are not P-a rows at all (P-c territory)
    with pytest.raises(ValueError):
        mod.pa_row_route(2, 2)
    # the pre-amendment blanket encoding is structurally impossible: a
    # multi-round coherent-backdrop row can never reach the (a) pin route
    assert all(mod.pa_row_route(r, 1) == "visibility" for r in (2, 3, 4, 7))
    # the STRUCTURAL pin spec itself is unchanged in label/threshold
    spec = mod.pin_spec("h2_t1_blindness_in_window")
    assert spec.label == mod.STRUCTURAL and spec.threshold == mod.PA_LAW_GAP_MAX
    assert "ruling 11" in spec.note


def test_seam_mass_visibility_table_rulings_12_13():
    # ruling 12: REPORTED feature table; ruling 13: 1e-1 (c) ceiling ONLY
    rows = [
        {"context": "r0:R2-L0", "rounds": 2, "repeats": 1,
         "tv_coherent": 6.3e-5, "tv_twirled": 1.2e-5},
        {"context": "eval:R4-ry", "rounds": 4, "repeats": 1,
         "tv_coherent": 1.83e-2, "tv_twirled": 7.9e-3},
    ]
    table = mod.score_seam_mass_visibility(rows)
    # the amendment-recorded toy worst case (1.83e-2) sits well inside 1e-1
    assert table["catastrophe_tripwire"] is False
    assert abs(table["ceiling"] - 1e-1) < 1e-15
    assert abs(table["worst_tv"] - 1.83e-2) < 1e-15
    assert "REPORTED" in table["disposition"]
    assert "ruling 12" in table["disposition"]
    # TV ~ O(1) trips the (c) catastrophe tripwire (build bug), never a band
    trip = mod.score_seam_mass_visibility(
        rows + [{"context": "broken", "rounds": 3, "repeats": 1,
                 "tv_coherent": 0.4, "tv_twirled": 0.0}])
    assert trip["catastrophe_tripwire"] is True
    # the registered constant is declared (c) in the class table
    assert mod.SEAM_MASS_VISIBILITY_CEILING == 1e-1
    assert mod.REGISTRATION_CLASS_TABLE["seam_mass_visibility_ceiling"]["class"] == "c"


def test_seed_robust_convergence_floor_on_bunching_arm():
    # R2-4/E-3: the at-floor clause is scored on the WELL-SPECIFIED tb_bunching
    # arm; the misspecified coherent arm's KL plays NO role in the floor clause.
    out = mod.seed_robust_convergence((1234.5, 1234.5), (1e-8, 2e-8))
    assert out["fit_converged_seed_robust"] is True
    assert out["bunching_arm_at_floor"] is True
    # the pre-fix encoding (coherent-arm at-floor) would have failed here by
    # design — the coherent composed family is registeredly misspecified.
    # bunching arm off floor on either seed => the clause fails
    assert mod.seed_robust_convergence((1.0, 1.0), (1e-3, 1e-8))[
        "fit_converged_seed_robust"] is False
    # coherent cross-seed NLL disagreement => fails (that clause is retained)
    assert mod.seed_robust_convergence((1.0, 1.0 + 1e-3), (1e-8, 1e-8))[
        "fit_converged_seed_robust"] is False
    assert mod.REGISTRATION_CLASS_TABLE["seed_robust_nll_tol"]["class"] == "c"


def test_oracle_kl_tv_record_level_branch_aligned():
    # R2-3: the adaptors' oracle comparators work on the EXISTING SeamStripLaw
    # public surface (measurement_record + probs) — no calibration.nll
    # delegation, no .detector_events/.observable reads.
    import inspect

    import torch

    ad = _adaptors()
    rec = torch.tensor([[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]])
    p = SimpleNamespace(measurement_record=rec,
                        probs=torch.tensor([0.4, 0.3, 0.2, 0.1], dtype=torch.float64))
    q = SimpleNamespace(measurement_record=rec,
                        probs=torch.tensor([0.25] * 4, dtype=torch.float64))
    assert ad.oracle_kl(p, p) == 0.0
    manual_kl = float((p.probs * (p.probs / q.probs).log()).sum())
    assert abs(ad.oracle_kl(p, q) - manual_kl) < 1e-15
    manual_tv = 0.5 * float((p.probs - q.probs).abs().sum())
    assert abs(ad.oracle_tv(p, q) - manual_tv) < 1e-15
    # zero-mass branches carry no KL (finite result)
    p0 = SimpleNamespace(measurement_record=rec,
                         probs=torch.tensor([0.5, 0.5, 0.0, 0.0], dtype=torch.float64))
    assert math.isfinite(ad.oracle_kl(p0, q))
    # misaligned enumerations refuse loudly (branch alignment is asserted)
    q_mis = SimpleNamespace(measurement_record=rec.flip(0), probs=q.probs)
    with pytest.raises(AssertionError):
        ad.oracle_kl(p, q_mis)
    with pytest.raises(AssertionError):
        ad.oracle_tv(p, q_mis)
    # regression pin: the joint_kl/.detector_events path is GONE (R2-3) —
    # checked on the CODE body only (the docstring legitimately cites the
    # removed delegation by name).
    import ast
    import textwrap

    fn_ast = ast.parse(textwrap.dedent(inspect.getsource(ad.oracle_kl))).body[0]
    body = fn_ast.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]  # drop the docstring
    code_only = "\n".join(ast.dump(stmt) for stmt in body)
    assert "joint_kl" not in code_only and "detector_events" not in code_only
    module_src = _ADAPTOR_PATH.read_text()
    assert "from qec_twin.calibration.nll import" not in module_src


def test_w2_gate_spectra_are_psd_score_fisher():
    # R2-5/E-4: the gate-spectrum source is the PSD per-outcome score Fisher
    # (outer-product form) — every eigenvalue >= 0 up to eigensolver round-off;
    # the indefinite init-point NLL Hessian is retired as a spectrum source.
    import torch  # noqa: F401  (toy carrier law below)

    from qec_twin.forward.scalable import ComposedCarrier, StripContext, StripSpec

    ad = _adaptors()
    spec = StripSpec(2, 2)
    carrier = ComposedCarrier.random(spec, num_kraus=2, seed=0, seam_phi_init=0.1)
    ctx = StripContext(rounds=1, label="R1-L0")
    obs = ad.observations_from_law(carrier.strip_law(ctx), ctx)
    eigs = ad.score_fisher_spectrum_set(carrier, [obs])
    n = ad.flat_parameters(carrier).numel()
    assert len(eigs) == n
    assert min(eigs) >= -1e-10  # PSD by construction
    # the single-context wrapper is the same object
    assert ad.score_fisher_spectrum(carrier, obs) == eigs
    # multi-context form: F(set) is additive => eigenvalue sum (trace) doubles
    eigs2 = ad.score_fisher_spectrum_set(carrier, [obs, obs])
    assert abs(sum(eigs2) - 2.0 * sum(eigs)) <= 1e-9 * max(sum(eigs), 1.0)
    # the gate encoding constant is declared (c)
    assert mod.REGISTRATION_CLASS_TABLE["w2_spectrum_contexts"]["class"] == "c"
    assert "score-Fisher" in mod.W2_SPECTRUM_CONTEXT_RULE


def test_fix_round_2_constants_declared_in_class_table():
    # section-E silent-constant declarations (all (c): gating/design only)
    for key in ("seed_robust_nll_tol", "edge_dof_visibility_floor",
                "decoder_mass_floor", "gradcheck_design", "map_test_constants",
                "tier0_z", "seam_mass_visibility_ceiling", "w2_spectrum_contexts",
                "stochastic_control_contexts"):
        assert mod.REGISTRATION_CLASS_TABLE[key]["class"] == "c", key
        assert mod.REGISTRATION_CLASS_TABLE[key]["source"], key
    # the derived decoder-floor bias bound travels with the declaration
    assert "6.6e-8" in mod.REGISTRATION_CLASS_TABLE["decoder_mass_floor"]["source"]
