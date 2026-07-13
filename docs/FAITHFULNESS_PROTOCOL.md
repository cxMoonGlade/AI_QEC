# Faithfulness Protocol — the anti-toy discipline (BINDING)

> **Why this exists.** Recurring "toys" (models that look right but are not faithful) have cost far more in
> downstream bug-hunting than they saved at build time. Root cause (2026-06-20): **circular verification** —
> each toy was checked against a reference that shared its own blind spot, so it passed. This protocol makes
> that structurally impossible. Token budget is unlimited; **slow is fast** — front-loaded rigor at build time
> costs far less than the 10× debug later. Binding for every **load-bearing model / faithfulness claim** (the
> "what does this represent" claims), enforced as required deliverables.

## Root cause (so we don't mis-medicate)
It is **not** mainly agent laziness — we gave agents **shortcuttable checks**. Every toy was verified against
something sharing its blind spot:
- lumped engine vs lumped DM oracle (both omit within-cycle) → Gate-4 passed;
- X-only / Y-dropped engine vs the matching oracle (both drop the echo) → Gate-4 passed;
- the `C_L=0` channel vs "our own qutip" (also `C_L=0`) → "matched";
- the `√E_b` instrument verified at R=1 (where the instrument is inert) → passed;
- `0.90` pinned with no reference at all.

Every toy that was **caught** was caught by a reference that **could not share the error**: the raw `.stim`, a
closed-form theorem, the literature, a from-scratch tokenizer (→ `1.5e-18`), the information–disturbance theorem.
**theory-first alone has a hole: when the theory is itself the shortcut, "run matches my prediction" passes with
both wrong.** This protocol closes that hole.

## The four rules (mandatory for every load-bearing faithfulness claim)

### Rule I — Ground truth INDEPENDENT of the implementation
Verify each load-bearing quantity against one of: the **raw artifact** (the circuit `.stim`, the dataset bytes,
the experimental paper), a **closed-form theorem/identity**, or a **from-scratch reconstruction** (a second
implementation sharing no code/assumption with the one under test). **NEVER** against a parallel model that could
share the same simplification. **A check against the engine's own oracle (or "matches our own qutip") is NOT
certification** if the oracle could share the omission. Certification = agreement with something that *cannot* be
wrong the same way.

### Rule II — Constraint ledger (theory-first, upgraded)
BEFORE building, enumerate the physical theorems/invariants the model MUST satisfy, and write a **falsifying
test** for each (it must FAIL LOUDLY when violated — confirm it actually trips on a broken input). **Standing
ledger (append every new pit; blood-bought):**
1. **Apply every physical gate the circuit contains.** Never drop a physically-applied gate on an "it's a
   frame / detector-invariant" argument (the X/Y DD echoes). Classify physical-pulse (unconditional transversal)
   vs frame (`CX/CY rec[..] q` / sweep-controlled) from the RAW circuit.
2. **Information–disturbance.** An instrument whose outcome distribution depends on a state property MUST disturb
   that property (the `√E_b` / "`|2⟩`-untouched + marginal=`E_s`" trap). The POVM effect ≠ the measurement
   instrument; at R=1 the instrument is invisible — test it at R>1.
3. **Clifford / detector / Pauli-frame-invariant ≠ dynamics-invariant.** A gate invisible to the Clifford
   picture can be decisive for non-Pauli (leakage / coherent) dynamics.
4. **CPTP + channel symmetries.** CPTP residual `< 1e-12`; check the channel's symmetries (WG is not `|0⟩↔|1⟩`
   symmetric, so any data Pauli reshapes leakage).
5. **Read the raw inputs end-to-end.** Don't infer structure from a convenient subset (r10 from r01) or assume;
   read the whole artifact.
6. **Underdetermined ⇒ bracket, don't freeze.** A quantity not fixed by the data/POVM → register a bracket of
   valid arms + report sensitivity; default = "representative," never "physical truth."
7. **Estimator convergence — no down-biased plug-ins.** Any sampled estimator must be convergence-checked: if it
   DRIFTS with N it is not converged ⇒ biased. Specifically, an in-sample Bayes-floor plug-in
   (`Σ_s min(P̂(s,f=0),P̂(s,f=1))` / `½(1−TV̂)`) in the under-sampled regime (`2^(8R) ≫ N`, high collision rate) is
   **down-biased — it RISES with N** — which **inflates `gap-to-Bayes` and manufactures a FALSE not-capped**
   (the ⑦ R=5 NOT-CAPPED artifact, 2026-06-21; the prior-program "floor lives at large R" pit). At large R use a
   held-out / cross-fit / exact-sub-register floor, never the in-sample plug-in at face value; report the
   `[honest, in-sample]` bracket. "A down-biased floor makes the verdict conservative" is BACKWARDS for
   not-capped — it makes it easier (a false positive).

### Rule III — Declare + BOUND every simplification
No undeclared model reduction. Each lump / pin / truncation / phenomenological substitution: (a) declared in the
pre-registration with its epistemic class (a/b/c per `METRICS.md`), and (b) its error **bounded** against the
faithful version. **An unbounded simplification is a STOP** — derive the bound or build the faithful version
first. (The lumping ×15, the `0.90` pin, the `C_L=0` channel all failed exactly here.)

### Rule IV — Freeze numerical provenance before the run
Every claim-bearing value must be classified as `paper-measured`, `paper-derived`,
`dataset-measured`, `calibrated-to-paper`, `project-design`, `convenience-default`, or
`numerical-only`, following `docs/NUMERICAL_PROVENANCE.md`. A paper equation grounds a form, not
silently the amplitude substituted into it. A transformed value carries the complete conversion /
calibration chain; a paper-backed value carries an exact page/figure/table/equation, units, device,
and protocol scope. A cross-paper or cross-device tuple is a **literature-scale composite benchmark**,
not a physical cell. Missing provenance is a STOP for a hardware/realism claim. Numerical tolerances,
resource caps, and software tripwires may never be laundered into physical evidence.

## Enforcement (structural, not exhortation)
1. **Required deliverables.** A model/faithfulness claim is not "done" until it ships: (i) the constraint ledger
   with each test passing (and shown to trip on a broken input), (ii) the independent ground-truth check
   (Rule I), (iii) the declared+bounded simplification list (Rule III), and (iv) a value-level provenance
   manifest satisfying Rule IV. The **builder** produces these BEFORE
   claiming done — front-loaded.
2. **From-scratch red-team by default.** Every faithfulness-critical model gets an independent adversarial
   reviewer whose job is to BREAK it against the raw artifact (un-led: stage problem + goal + artifact only).
   This is what caught the X/Y echoes.
3. **Orchestrator duties.** Bake these rules + the standing ledger into every builder/reviewer brief (template
   below); certify only via from-scratch independent reconstruction; never accept a circular check; personally
   read the raw source for load-bearing "what does this represent" claims.

## Agent-brief template snippet (prepend to every builder/reviewer brief)
```
ANTI-TOY PROTOCOL (binding — docs/FAITHFULNESS_PROTOCOL.md):
- Verify every load-bearing quantity against an INDEPENDENT ground truth (raw artifact / closed-form /
  from-scratch). NEVER certify against a parallel model that could share your simplification — a check vs the
  engine's own oracle or "our own qutip" is NOT certification (circular verification is how every toy slipped).
- BEFORE building, write the CONSTRAINT LEDGER: the physical invariants this model must satisfy + a falsifying
  test each (confirm each test trips on a broken input). Apply every physical gate the real circuit contains.
- DECLARE + BOUND every simplification (epistemic class + error vs the faithful version). Unbounded = STOP.
- FREEZE every claim-bearing number's provenance kind, exact source locator, units/scope, and transformation
  chain. Cross-paper/device tuples are composite benchmarks; numerical/software gates are not physical evidence.
- Your deliverable is NOT "done" without: the ledger (passing) + the independent ground-truth check + the
  bounded-simplification list + the numerical-provenance manifest.
```

## Living document
Append every new toy/pit to the standing ledger (Rule II) with the failure that motivated it, so the protocol
sharpens over time. Pits encoded so far: the leaked-readout `0.90`; the `C_L=0` channel; the `√E_b` instrument;
the dropped X echo; the dropped Y echo; the within-cycle lumping (×15); the r01→r10 inference; the
"drop `stab_supp_isx`" slip; the Miao/McEwen cross-device preset; the Gaussian-surrogate versus
finite-RTN CP-divisibility mismatch; the R1-only entropy artifact reported as multi-round. See also:
`docs/NUMERICAL_PROVENANCE.md`, `docs/METRICS.md` (epistemic-status declaration), and the per-module READMEs.
