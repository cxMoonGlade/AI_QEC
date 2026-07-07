---
name: contract-build
description: The contract-first adversarial build pipeline that produced this repo's clean first-run builds (OPT2-1 batched-MPS core 22/22, P2-ii per-round seam 5/5, API-hardening waves). Use this skill whenever starting ANY nontrivial build in this repo — a new src module, a multi-file feature, a refactor with behavior guarantees, a test-suite addition, or wiring a new seam — even if the user just says "build X", "implement the next phase", "开工", or names a roadmap item (OPT2-x, P2-x, Wave-x). Also use it when a build is going sideways (gates failing for unclear reasons, review findings piling up post-hoc) to re-anchor the process.
---

# Contract-first adversarial build

The pipeline below is why recent builds passed their gates on the first real run.
The single load-bearing idea: **move every possible failure to the cheapest stage
that can catch it.** A design flaw caught at the contract stage is a text edit; the
same flaw caught after a GPU run is corrupted evidence, a re-run, and a re-review.
Every stage exists to starve the stages after it of failure modes.

Measured effect in this repo (2026-07-06/07 arc): 4 contract red-team passes drove
blockers 6→2→1→0 before any code ran; build reviews confirmed 8/9 and 14/15
findings pre-run; the first GPU gate runs then passed 22/22 and (after one
harness-side fix caught by its own precondition assert) 5/5. The expensive
resource — GPU evidence runs — was never spent on buggy code.

## Stage 0 — Ground before designing

Read `docs/CODE_MAP.md` first, then the actual seams the build touches (the real
functions, not their names in a plan). Verify the structural facts the design will
rest on and RECORD them in the contract ("the CSR marshal is content-independent
for leak — verified at sv_sampler.py `_emit_leak`"). A design premise you did not
verify is a blocker you scheduled for later.

If the mechanism/observable is physics, `theory-first` applies before this skill.

## Stage 1 — Write the contract, commit it before code

A design contract in `docs/twin_validation/` (or the operative prereg), committed
before any implementation. It must pin, explicitly:

- **Representation + invariants** (shapes, padding conventions, tracked state like
  an orthogonality center — with a per-op pre/post-condition table).
- **Every op with its referee**: which existing implementation each new unit is
  equivalent to, and the exact tie-break/guard semantics (`<=` vs `<`, fallback
  indices, degenerate-input behavior) — a registry, so nothing gets "harmonized"
  silently. Cite anchors by NAMED convention tags, not line numbers (lines rot).
- **Units on every threshold** (the λ-vs-σ lesson: a squared-scale misread moves a
  validity domain by orders of magnitude).
- **Registered gates**: what will be tested, at what tolerance, on what inputs,
  with the prediction written down (predict-before-measure: ALL gates pass; a miss
  is a finding to adjudicate, never a silent tolerance bump).
- **Scope fences**: what is deliberately NOT in this phase, so builders cannot
  drift into it.

## Stage 2 — Red-team the contract, loop until zero blockers

Spawn un-led adversarial reviewers ON THE CONTRACT (they get the contract + the
referee code, and the instruction to BREAK it: find a claim a gate cannot certify,
a semantics the contract fails to pin, a check a correct implementation would
fail). Classify findings blocker vs amendment. Adopt fixes as contract edits and
re-check with a fresh focused pass. **Loop until blockers = 0** — convergence is
the criterion, not a fixed round count. Do not start building on a contract with
open blockers: every one becomes code-stage rework at ~10x cost.

Typical catches at this stage (real examples): a numerically unsound tolerance
claim (Gram κ² breaking a 1e-12 gate), a gate that compares a thing to itself
(identical cap tuples), a required per-shot operator form the API lacked entirely.

## Stage 3 — Build with disjoint ownership, in parallel

Two builders, one file each, both given the CONTRACT as the binding spec:

- The module builder implements the contract.
- The test builder writes the registered gates **against the contract, not the
  implementation** (it runs in parallel — it literally cannot see the code). This
  is what keeps tests from inheriting implementation bugs.

Ban builders from GPU/pytest execution (static checks + `py_compile` +
`--collect-only` only) — evidence runs stay serialized with the orchestrator.
Where a signature is ambiguous, the test builder writes ONE thin adapter at the
top of its file (one place to fix), never scattered guesses.

## Stage 4 — Un-led multi-lens review, adversarially verified, fixed BEFORE any run

- Reviewers get problem + goal + artifacts ONLY (no diagnosis, no expected
  answers — leading a reviewer buys agreement, not scrutiny).
- Distinct lenses, not redundant copies: correctness/conventions, numerics/GPU,
  and a **vacuity/devious lens** whose one question is "what is the most devious
  implementation that still passes these tests?" (this lens finds the dead seams,
  the existence-check-only fakes, the identity-permutation blind spots).
- EVERY finding then goes to an independent verifier instructed to REFUTE it by
  reading the code. Only confirmed findings cost fix effort; the refuted ones are
  recorded, not acted on.
- Apply all confirmed fixes, then run gates. The first evidence run should be on
  code you already believe is clean — if review findings are still open when the
  GPU starts, the run is pre-corrupted.

## Stage 5 — Gates, evidence, and the nets

- Gates run via committed runner scripts: literal `$`-free PATH export inside the
  runner, sha256 of the sources printed into the log, `exit ${PIPESTATUS[0]}`.
- **Refactor claims get byte-identity proof, not assertion**: capture a baseline at
  the pinned pre-change commit (git worktree + `PYTHONPATH` override + printed
  `module.__file__` evidence that the right code was imported), hash the outputs,
  compare against the working tree. "Pure addition" is a hash equality, not a
  belief.
- Full suite after every wave; read counts from **junitxml**, never from progress
  dots (test stdout interleaves with the dot lines and silently eats them) and
  never from the summary line (a teardown crash can eat it — count FAILURES and
  the [100%] marker, or parse the XML).
- A failing gate first asks: gate miss, or precondition/harness bug? The greppable
  `PRECONDITION (class c, not a gate miss):` prefix exists exactly to make this
  triage instant.

## Stage 6 — Two-sided test verification (the devious standard)

Tests are code too, and this arc's data says they carry MORE defects than the
modules they gate. Two directions, per unit:

- **Should-fail-must-fail (KILLERs)**: every load-bearing assert ships a sabotaged
  variant DEMONSTRATED to trip it (`assert_control_trips`); a check never shown to
  fail is unproven. Check new tests against the K-catalog in
  `tests/_support/README.md` (K-1 inert seam … K-10 measurement-isolation
  contamination) and add the discriminators that kill your matrix's survivors.
  Sabotages that pattern-match reality: constant/reversed indexing, transposed
  layouts, strict-vs-nonstrict tie-breaks, existence-check-only fakes.
- **Should-pass-must-pass-robustly**: tolerance asserts carry measured margins
  (a pass within 10x of its threshold is EVIL-MARGINAL — the measured
  1.181e-12-vs-1e-12 case would have flipped on a parameter breeze); skips match
  the registered allowlist (`tests/_support/skip_allowlist.json` — an unregistered
  skip is how a deleted API silently stops being tested); preconditions never fire
  in the committed suite.

Expect the standard to catch YOU: in this arc it caught its own author twice
(an all-zero record making a transpose killer vacuous; a "random asymmetric"
pattern that was secretly the identity matrix). That is the standard working.

## Stage 7 — Close the loop

- Backfill OUTCOMES into the contract/prereg: gate results with hashes, every
  miss recorded as a finding with its adjudication (harness-side vs module-side).
- Regenerate `docs/CODE_MAP.md`; update the owning module's README.
- src/tests commits wait for explicit user confirmation (docs flow normally);
  one reviewed diff per phase.
- Out-of-scope defects found along the way become chips/tasks, never scope creep.

## Independence rule (binds every stage)

An anti-circular referee may live in a shared library, but must share NO
implementation code with the arm it referees — independence means "no shared
code", not "rewritten every time". Fixtures, cell builders, packing helpers, and
runners centralize freely; a referee's blind-spot profile does not. When a copy
stays local for this reason, mark it: "deliberately local, referees X, must not
import Y".

## Sizing

Small change (one function, doc-level): stages 1–2 collapse into a design pin
paragraph in the operative prereg + one focused reviewer; stages 4–5 stay.
Full module: run every stage. When unsure, price it by the cost of a corrupted
evidence run — if the gate run is expensive or the claim is load-bearing, the
full pipeline is cheaper than one bad run.
