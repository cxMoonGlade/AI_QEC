# Numerical value-lifecycle cleanup handoff — 2026-07-16

## Status at session boundary

This phase is **not yet globally GREEN**. The worktree is intentionally left uncommitted and
unstaged. Do not reset, clean, or discard it. The latest source edit has only targeted validation;
the complete owner suite, documentation synchronization, isolated wheel, full test suite, and
canonical service acceptance remain pending.

The phase goal is broader than isolated arithmetic fixes: every current public value must preserve
its declared meaning through

`construct -> emit -> manifest -> save/load -> consume`.

The implementation strategy is:

- keep the ordinary binary64 path in the established interior domain;
- use one shared range-aware primitive for dangerous scaled products and log-odds shifts;
- form boundary-sensitive physical expressions and sums exactly from their binary64 inputs, then
  round once;
- reject an unrepresentable value instead of fabricating zero, one, infinity, or a finite floor;
- validate and snapshot values at the nearest public boundary with an input-named error.

## Latest completed evidence

- The probability endpoint probe is complete and bound to
  `src/error_coupling_simulator/numerics.py` SHA-256
  `3c966d2e3fb67d24632de99633ee74445cf516d4ddbe3aa944222a042a73d683`.
- Main grid: 22,000 points, mpmath 1,600 dps, 0 false accepts, 0 false rejects, and 0 wrong
  endpoint outputs.
- Cross-scale supplement: 1,326 points, mpmath 1,800 dps, 0 false accepts, 0 false rejects,
  0 wrong outputs, and maximum 0 ULP.
- Scaled-exponential supplement: 208 points across half-subnormal and overflow boundaries,
  0 misclassifications and maximum 0 ULP.
- The probe verified its source hash at start and finish and left no child process running.
- The latest PhaseBurst regressions both pass:

  ```text
  tests/test_source_process_units.py::test_phase_burst_recovery_preserves_finite_tail_when_elapsed_ratio_overflows
  tests/test_source_process_units.py::test_phase_burst_accumulates_simultaneous_events_before_float64_rounding
  2 passed
  ```

## Latest source behavior

`src/error_coupling_simulator/numerics.py` owns the shared scaled-exponential multiplication,
scaled product/ratio, and odds-domain probability shift. There are no probability-floor helpers.

`src/error_coupling_simulator/source/process.py` now includes these additional boundary repairs:

- PhaseBurst recovery forms `amplitude * recovery / (recovery + lag * cycle)` from exact binary64
  input ratios, without first forming an overflowing elapsed time or elapsed/recovery ratio.
- All PhaseBurst event contributions to one cycle/site are accumulated as `Fraction` values and
  rounded once. The fixed three-event case whose sequential partial sum reaches `-inf` but whose
  final value is `-0.943601... * DBL_MAX` now succeeds.
- SourceTimeline rejects negative timeline, baseline, ablation, explicit independent, and metadata
  baseline seeds at the relevant public boundary.
- SourceTimeline metadata is deep-copied, recursively restricted to JSON-compatible types, and
  rejects non-finite numbers. `to_manifest()` canonicalizes NumPy metadata to JSON values.
- Degenerate Storm metadata represents infinite correlation length as
  `correlation_length_cycles=null` with
  `correlation_length_cycles_status="structural_infinite_limit"`; it does not emit non-standard
  JSON `Infinity`.
- Exact artifact summaries retain shape, dtype, native min/max, and SHA-256. `mean` and `std` were
  removed because they could turn a nonzero subnormal statistic into zero, overflow a finite
  standard deviation to infinity, or narrow an exact integer extrema through float64.
- The defensive empty-`pauli_error` corruption guard was restored; construction-time nonempty
  validation does not replace consumer-side fail-closed checks while the stored mapping remains a
  deliberate corruption seam.

## Known RED / unfinished work

1. The last independent full source-process run preceded the newest edits and reported
   `86 passed, 2 failed`. Both failures are stale test assertions that still expect the removed
   manifest `mean`/`std` fields:
   - `test_L0_to_manifest_structure_and_seed_branches`
   - `test_helper_array_summary_numeric_and_non_numeric`
   Update those assertions to the exact-artifact summary contract, then rerun the entire owner
   file. Do not restore lossy statistics merely to turn the tests green.
2. Rerun the complete source-process coverage registry. New helpers and public behavior changed the
   previous 33-unit accounting.
3. The read-only phase-diff reviewer was stopped at the session boundary. It had not issued a final
   clean verdict after the exact PhaseBurst accumulation patch and strict metadata patch. Perform a
   fresh hostile review before declaring focused GREEN.
4. Synchronize `docs/NUMERICAL_PROVENANCE.md`,
   `docs/simulator_validation/CLEANUP_AUDIT_2026-07-14.md`, `docs/METRICS.md`, and the relevant
   module README with dated RED/GREEN rows. Preserve all earlier RED history.
5. Regenerate `docs/CODE_MAP.md` only after source/test edits stabilize.
6. The newest work has not run the combined focused suite, isolated sdist-to-wheel install, full
   `pytest`, or the 71-file fresh-process service acceptance. The retained PEPS/FET entropy gate
   must remain red if its scientific discrepancy is unchanged; do not skip or weaken it.

## Immediate restart sequence

1. Read `docs/SIMULATOR.md`, `CLAUDE.md`, this handoff, and the tail of
   `docs/simulator_validation/CLEANUP_AUDIT_2026-07-14.md`.
2. Inspect `git status --short` and `git diff`; preserve all current user/worktree changes.
3. Do not edit or promote these quarantined untracked drafts:
   - `docs/papers/reading_notes/miao_leakage_transport_2211.04728v1.md`
   - `docs/simulator_validation/MIAO_2211_04728_CLAIM_AUDIT_2026-07-15.md`
4. Fix only the two stale summary assertions, run their RED/GREEN targets, then run
   `tests/test_source_process_units.py` in full.
5. Run a fresh read-only review of the five semantic source files and their tests. Any new behavior
   defect must receive its own public-path RED before a source fix.
6. Present the resulting semantic-lane `git diff` for user review before the focused GREEN gate.
7. After approval, synchronize evidence docs, rebuild the code map, and execute focused -> isolated
   wheel -> full pytest -> canonical acceptance in that order.

## Session discipline

- No files were staged or committed in this session.
- No compatibility layer, allowlist, skip, or probability floor is authorized.
- Do not interpret the completed probability probe as a global phase pass; it certifies only the
  current shared probability/scaled-exponential boundary implementation.
- A new session should continue from this worktree, not recreate the phase from historical Twin
  documents or old artifacts.
