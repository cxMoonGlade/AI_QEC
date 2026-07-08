# Stage-D test-API completion — L2-forward + exemption-challenger (design)

Motivation (user, 2026-07-07): "why do the D1 tests have so much to fix — is the test API
incomplete?" Root-cause triage of the D1 review findings put the biggest bucket in **class B:
defects a MECHANICAL layer should have caught but didn't, because it was deferred**. Two API
pieces close that bucket so future batches (certify D4/D5 onward) catch these automatically
instead of by human review. Build + test AFTER Workflow #1 lands (avoid CPU contention with the
running builders; and mutmut's output format must be seen before a parser is written).

## Finding: mutmut 3.6 interface
`mutmut run --help` exposes only `--max-children` (+ optional MUTANT_NAMES). **ALL config is
read from `setup.cfg [mutmut]`** (keys the pilot proved: `source_paths`,
`pytest_add_cli_args_test_selection`, `also_copy=src`). There is NO `--paths-to-mutate`/`--tests`
CLI. So a per-batch runner must (a) BACK UP the committed `setup.cfg`, (b) write the batch's
`[mutmut]` section, (c) run mutmut, (d) parse results, (e) RESTORE `setup.cfg`. Batches run
SERIALLY (no setup.cfg race). `mutmut` runs in a `mutants/` sandbox copy -> `also_copy=src` is
mandatory (else the tests' package imports fail — the pilot's key finding).

## Piece 1 — L2-forward: `outputs/twin_validation/stage_d_mutation.sh <registry>`
- Derive `source_paths` = the registry's `reconcile_modules`; `pytest_add_cli_args_test_selection`
  = its `covered_by_test_files`; `also_copy=src`.
- Back up `setup.cfg` -> write the batch `[mutmut]` -> `mutmut run --max-children 1` (serial;
  the workstation is the user's live desktop) -> `mutmut results` -> restore `setup.cfg`.
- **Gate: kill-rate >= 90%** per batch (the pilot's bar). Survivors triaged: each is either
  killed by a new test or registered as an equivalent-mutant exemption (reason) in a survivors
  registry json `tests/_support/stage_d_<tag>_mutation_survivors.json` (same shape as the
  pilot). This is the layer that would have MECHANICALLY caught the D1 "drop-P2 KILLER wrong
  direction" and "F6 wrong-direction" defects (a surviving/equivalent mutant is reported, not
  left to review).
- CPU-only for the CPU-pure batches. Heavy modules (carrier's exact-DM dual_point) will be slow
  — that is the cost of L2; run serially, budget accordingly (slow is fast).
- OPEN (resolve when first run): the exact `mutmut results` output format for the survivors
  parser — DO NOT write the parser blind; run once on the known-good D1 batch, read the real
  output, then parse.

## Piece 2 — exemption-challenger: `wave2_6_coverage_audit.py --challenge-exemptions`
An opt-in audit flag (default OFF -> Wave-2.6 / running gate unaffected). For every registered
exemption of kind `line`/`branch` (a "structurally unreachable" claim), the challenger tries to
REACH the branch and REJECTS the exemption if it can — this is the mechanical form of the D1
finding-2 catch ("dead branch" was reachable via float underflow).
- MVP: the exemption must carry a `challenge` spec = a committed test that DELIBERATELY drives
  the unit with adversarial inputs (float underflow 1e-300*1e-300=0, boundary 0/1, signed,
  empty) and asserts the branch stays unreached; the audit runs that test UNDER COVERAGE and
  confirms the exempted arc is still in `missing_branches` (if the challenge test REACHES it,
  the exemption is bogus -> hard error). If no `challenge` spec, a `line`/`branch` exemption is
  rejected (forces the author to prove unreachability, not assert it).
- Cheaper interim (no coverage re-run inside the audit): a `challenged_by` test name (must
  exist) that is itself an adversarial-input probe — necessary-not-sufficient, but better than
  the bare `covered_by` existence grep (finding 4). Prefer the MVP once built.
- The strongest guard remains: **prefer COVERING the branch with a real input over exempting it**
  (what D1 ended up doing — the underflow L0 test, 6/6 branch, no exemption). The challenger is
  the backstop for genuinely-defensive branches.

## Sequencing (user chose "A")
1. Workflow #1 finishes (build+verify the 4 quantum_bath batches).
2. Orchestrator integrates: serial gate re-run (authority) + triage verify findings + fix.
3. Build + test Piece 1 on the known-good D1 batch, then RETRO-run it on the 4 quantum_bath
   batches (authoritative kill-rate evidence). Fix survivors.
4. Build Piece 2 into the audit; wire both into the per-batch flow.
5. certify (D4/D5) onward: every batch = coverage gate (100/100) + mutation gate (>=90% kill)
   + exemption-challenger, all mechanical — human review becomes the backstop, not the front line.
