# Finite-RTN exact reduced-map diagnostic — stress test (2026-07-13)

## Adjudicated claim

For the project-design defaults of `OneOverFDriftSource`, each of two explicitly declared
longitudinal free-induction lifts—continuous symmetric CTMC and cycle-held phase accumulation—has
a positive BLP information-backflow witness within 200 cycles. This is a diagnostic reduced-map
claim only. It is not a claim about the production source fan-out, QEC channel/instrument,
syndrome-record memory, process-tensor memory, or logical error rate.

Inputs:

- literature closure: [`finite_rtn_exact_cpdiv_literature_closure_2026-07-13.md`](finite_rtn_exact_cpdiv_literature_closure_2026-07-13.md);
- prediction/gate document: [`finite_rtn_exact_cpdiv_prereg_2026-07-13.md`](finite_rtn_exact_cpdiv_prereg_2026-07-13.md);
- result: [`finite_rtn_exact_cpdiv_result_2026-07-13.md`](finite_rtn_exact_cpdiv_result_2026-07-13.md);
- bound artifact content hash: `de04160d0c5a2d22a773fbeffe8805c3c2be7a6d68c7239daa09e528d99c5ffd`;
- clean execution commit: `e35ff7d89ef6e656b8e0205abae0753630459f7d`.

## Trip-wire audit

| wire | adversarial check | outcome | propagation consequence |
|---|---|---|---|
| symmetry / theorem | Re-derive the symmetric-RTN coherence using the paper's per-direction rate convention and check strong/weak branches. | **pass** for the two declared free-induction objects; exactly 3 of 8 modes are strong. | Named diagnostic claim survives. |
| formulation invariance | Compare continuous CTMC and cycle-held lifts; then compare both with the actual production coupling path. | Both lifts are BLP-positive, but production fans `z_r` through `SourceCouplingConfig` rather than applying either free-induction Hamiltonian. | Diagnostic survives; production claim is **reopened/open**. |
| rate vs observable | Ask whether source autocorrelation, reduced-map backflow, record Markov order, and LER were being conflated. | They are different objects. The source alone has no CP-divisibility property. | No source-level, record-level, or LER wording may inherit the result. |
| independent ground truth | Compare factorized formula against full `2^8` CTMC Feynman–Kac and transfer-matrix oracles; independently reconstruct without importing the implementation. | Max errors `1.33e-15` and `1.55e-15`; unled reconstruction agrees to floating-point precision. | Implementation and convention checks pass. |
| degenerate design / corruption | Test Gaussian and all-weak negative controls; deliberately use the wrong factor-of-two rate and omit one mode. | Controls have zero positive excursion; corruptions produce `0.09311` and `0.09180` oracle mismatch. | The gate is sensitive to the intended mechanism rather than automatically positive. |
| suppressing lens | Ask whether free induction omits the quarter-CZ/measurement/reset instrument or can hide/cancel a revival. | Yes; the actual fan-out and instrument are absent. No bound transfers the lift to the full record. | **STOP** every production-QEC/notion-1/record inference. |
| preregistration integrity | Check whether the prediction document and script were committed before first result inspection. | **fired**: the first run occurred while both were uncommitted. The current rerun is clean, bound, and reproducible, but history is not pristine. | **STOP** the label “pristine Git-preregistered prediction”; retain “independently reproduced exact diagnostic.” |
| downstream propagation | Search binding/status/handoff docs for the old source-level `1/f is CP-divisible/twirled` slogan and for long-range acceptance by local tensor metrics. | Wording was narrowed; production bridge remains open. Long-range record-faithfulness evidence remains missing. | No downstream upgrade; long-range work stays **STOP / reopen evidence**. |

## Independent-review deltas

Hostile review initially found that the grid could veto an analytic witness, `t0+1` was formed
outside the high-precision context, implementation failure and scientific null were conflated,
raw oracle rows and provenance bindings were absent, and monotone controls could serialize a
negative “maximum positive” value. The committed gate now:

1. adjudicates the continuous result from the analytic zero and high-precision recovery, with the
   grid explicitly descriptive;
2. separates implementation gates from diagnostic verdicts;
3. binds clean tracked inputs by SHA-256, Git blob, and commit;
4. serializes the registered oracle rows, full held sequence, and argmax brackets; and
5. clamps the maximum-positive control statistic at zero.

A delta audit of the current commit and artifact passed all five repairs. This repair trail is
part of the evidence and must not be compressed into an unqualified `PASS`.

## Final adjudication

- **`SURVIVES CURRENT WIRES`**: the exact, independently reproduced, diagnostic-only BLP-positive
  result for the two named free-induction lifts.
- **`STOP`**: describing its history as a pristine Git-preregistered prediction.
- **`STOP / OPEN BRIDGE`**: every inference to the production QEC dynamical map, full syndrome
  record, notion-2/notion-3 memory, PEPS record fidelity, or logical error rate.

The next admissible notion-1 step is a separately preregistered bridge that implements or bounds the
actual `z -> Theta -> quarter-slice channel/instrument` path. It must not reuse this diagnostic as
its ground truth.
