# Body review — Dong, Wang, Khan, "Efficient learning and optimizing non-Gaussian correlated noise in digitally controlled qubit systems"

## Provenance
- **Source:** arXiv:2502.05408v2 (Feb 2025, v2 Jun 2025), Virginia Tech / CAS / Dartmouth;
  fetched 2026-07-02, cached `outputs/papers/2502.05408.{pdf,txt}` (36 pp).
- **Reading method:** BODY-READ (declared level, HANDOFF §4.6): abstract + Sec. I intro +
  contribution statement + structure scan read; frame-based formalism (Secs. II–III),
  complexity bounds, and numerics not worked through. Keyword sweep: `syndrome` 0,
  `stabilizer` 0, `gauge` 0 — active-control QNS; no QEC records, no unlearnability
  characterization.
- **Why now:** user-caught coverage gap — nearest QNS-family neighbor extending the
  Paz-Silva line; checked against Bones B/#3 before resolving their no-owner verdicts.

## Executive summary
Quantum noise spectroscopy under **digital control** (effectively instantaneous pulses) for
**non-Gaussian, spatio-temporally correlated dephasing**: combines frame-based
characterization (filter functions on a control-adapted frame) with a control-based
symmetry analysis to get higher-order spectral estimation and noise-optimized circuit
design. Headline structural claim: for digitally driven qubits, the resources for
characterization-and-control scale with the **complexity of the applied control** (circuit
size), NOT with the intrinsic non-Gaussian truncation order of the environment — so some
non-perturbative dynamics become addressable with modest control repertoires. Provides
complexity bounds for learning high-complexity noise; single- and two-qubit numerical
demonstrations (spectral estimation → dynamics prediction → circuit optimization).
Authors state the approach is not generally scalable; value case = open-loop
control-based fault tolerance with minimal distributional assumptions.

## Relevance to the coupling simulator
1. **B.1 / #3.1 no-owner verdicts unaffected.** Access model = ACTIVE designed control
   (chosen pulse sequences/frames — the QNS pole, same family as Paz-Silva/von Lüpke and
   Montañà-López 2511.16772); object = noise spectra/polyspectra in a control-adapted
   frame; question = positive estimation protocols + control optimization. No fixed
   passive machine, no stabilizer records, no gauge/blind-spot characterization
   (keyword-swept), no QEC data, no PSD-constrained estimation with physicality
   guarantees. The B and #3 conjunctions stay empty.
2. **Sharpens our Gaussianity honesty (Step 0.α).** They attack exactly the assumption we
   declare: our Σ-model is Gaussian by DECLARED model class (with quasistatic/1-f anchors),
   not by theorem. Cite as the state of the art for what lifting Gaussianity costs
   (higher-order spectra, control-complexity-bounded) — one sentence in the boundedness
   discussion of the model-provenance step; it strengthens, not weakens, the declared-class
   framing (non-Gaussian learning exists but demands a control repertoire passive records
   do not have).
3. **Landscape row.** In the positioning table's QNS/active family row, list alongside
   Paz-Silva (foundational-exempt if cited at all) with this as the recent non-Gaussian
   digital-control endpoint — satisfies the citation recency policy.
4. **One reusable idea (flagged, not adopted):** their "control complexity, not noise
   complexity, bounds what the dynamics can express" resonates with our fixed-schedule
   setting — the stabilizer schedule IS a fixed digital control sequence, so the record law
   can only expose noise functionals the schedule's effective frame reaches. That is
   qualitatively our accessible-span story; if a referee asks for a QNS-language bridge,
   this is the citation to build it with. No derivation dependence today.

## Trust
Body-read only — cite for positioning/landscape and the non-Gaussian-cost statement;
re-read Secs. II–III before relying on any specific frame-function result.
