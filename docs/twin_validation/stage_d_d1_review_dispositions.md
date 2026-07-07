# Stage-D batch D1 — un-led review findings + dispositions

Independent adversarial review of D1 (`quantum_bath/observables.py`, 7 units) + the
generalized coverage gate, 2026-07-07 (reviewer agent, un-led: given problem+goal+artifacts
only, no diagnosis). Verdict: **FIX-FIRST**. Every finding was re-verified before acting; the
load-bearing gate holes (F1, F5) were reproduced as self-test mutants C/D that MISSED pre-fix
and BITE post-fix. All fixes landed; D1 gate + gate self-test (5/5) + Wave-2.6 back-compat all
green.

| # | sev | finding | verified? | disposition |
|---|-----|---------|-----------|-------------|
| F1 | HIGH | `out_of_scope` was an unguarded under-population bypass: a real CPU-pure unit could be parked as `gpu_bound` with a false reason and dropped from scoring — the game the AST reconcile claims to close. | YES (self-test mutant C MISSED pre-fix) | **FIXED** in `wave2_6_coverage_audit.py`: `out_of_scope` entries must be `{class∈{gpu_bound,quimb_bound,retracted,deferred}, reason, covered_by(non-empty+exists)}`; `gpu_bound`/`quimb_bound` are STRUCTURALLY REFUTED if the unit's module imports neither torch nor quimb (`_module_imports`) — a pure numpy/math unit cannot be parked as gpu_bound. Mutant C now BITES (`FALSE-OUT-OF-SCOPE-CLASS`). |
| F2 | MED-HIGH | The `exact_cmi_bits` `if den>0 and num>0` exemption claimed the False arc is "unreachable for ANY dict" — FALSE: a valid normalized distribution with a tiny term underflows `num=p*P2` to 0.0; signed entries zero `den`. It is a LIVE log2 guard. | YES (underflow input reaches the arc) | **FIXED**: exemption REMOVED; added `test_L0_exact_cmi_bits_underflow_reaches_guard_false_arc` (a valid non-negative normalized distribution `{(0,0,0):1e-200,(1,1,1):1-1e-200}` with an underflow-to-0.0 precondition assert) so the arc is covered HONESTLY. `exact_cmi_bits` now scores branch 6/6 with NO exemption. Deleted the false-invariant "proof" test. Docstrings corrected. |
| F3 | MED | "100% branch" was vacuous (0/0) for 4 units (`K_stat_joint`, `K_stat_binary`, `tv_distance`, `record_distance`): coverage.py emits no branch arc for comprehension bodies, so the headline overstated what was verified. | YES (gate shows 0/0) | **FIXED (honesty)**: docstring table now states "none tracked (comprehension; 0/0)" for those 4 units and notes their faithfulness rests on the L1 property, not a branch count. (The 0/0→1.0 empty-denominator convention is coverage.py-standard; kept.) |
| F4 | MED | `covered_by` existence is a `def <name>` grep — it does not verify the named test covers the exempted arc (repointing at an unrelated existing test passes). | YES (reviewer PROBE2) | **DOCUMENTED + mitigated**: D1 now has ZERO exemptions and empty `out_of_scope`, so no live exploit. For the load-bearing case (gpu_bound oos) the discriminating guard is the STRUCTURAL `_module_imports` check (F1), which a false claim cannot satisfy. Full arc-attribution (run each covered_by test under coverage, confirm it hits the arc) deferred to Stage E; caveat added to `_covered_by_exists`. |
| F5 | LOW-MED | A per-unit `target` override could silently relax a unit below 100% (e.g. 0/0). | YES (self-test mutant D MISSED pre-fix) | **FIXED**: a per-unit target below `default_target` is a `TARGET-BELOW-DEFAULT` hard error unless it carries a valid `target_waiver` (reason + existing covered_by). Mutant D now BITES. |
| F6 | LOW | `test_KILLER_k_stat_nonneg_...` bit, but its comment ("signed sum can be negative") was factually wrong on its input (signed=+0.5). | YES | **FIXED**: reworked to use an OVER-normalized skip (sums to 2) so the signed sum is genuinely −1 < 0 — the dropped-abs mutant now actually VIOLATES K≥0, matching the test name; comment corrected. |
| F7 | LOW | Documented `iff`/metric gaps + thin coverage: tv/record "==0 iff equal" is not a theorem on mismatched support; `K_stat_binary` had no L1 property; `M_mem_stat≥0` is trivial with no KILLER. | YES | **FIXED**: docstring now states the SHARED-SUPPORT contract and drops the unqualified "iff"; added `test_L1_k_binary_zero_on_exact_marginal_and_nonneg`; added `test_KILLER_mmem_zero_on_markov1_would_fail_for_no_divide_variant` (the discriminating teeth for M_mem is the ==0-on-Markov property, now demonstrated). |

**Reviewer positive confirmations (unchanged, verified correct):** CMI≥0 holds (min 8.7e-7 over
300k random joints; the −1e-9 slack is safe); the Markov-1 `==0` claim is a true theorem for both
CMI and M_mem; the CMI inverted-ratio KILLER genuinely bites; the project_axis overwrite KILLER
bites; the AST line-set derivation + stale-line/stale-callee guards work.

**Post-fix evidence:** D1 gate PASS (7/7 at 100/100, exact_cmi_bits 6/6 branch no-exemption);
gate self-test PASS (5/5 mutants: control OK + A/B/C/D BITE); D1 test file 18 passed; Wave-2.6
default-mode back-compat PASS (19 units); CPU additive co-run green.
