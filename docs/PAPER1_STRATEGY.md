# Paper-1 publication strategy (adversarial-referee verdict + legal-comparison constructions, 2026-06-11)

> Source: three-party adversarial exercise (advocate / prosecutor / adjudication, archived in
> full under `docs/.reports/paper_panel/`: `advocate_case.md`, `prosecutor_case.md`,
> `adjudication.md` — every citation verified line-by-line against `docs/metric_results.md`).
> This file is the executive summary of the adjudication + the legal-comparison construction
> plan confirmed by the project owner. The two-paper split is at the end.

## Verdict

**(ii) Sufficient for *Quantum* once the named additions land; the core finding (the
bunching chain) is not self-congratulation — it is the paper's hardest asset.** After a
literature sweep, the prosecution's ten exhibits formally conceded it cannot be diminished:

> exact identity decomposition f̂ ≡ r̂·R̂ (2.5e-16) → per-window split-replicated bunching
> spectrum R̂ ∈ [1.000, 17.7] (split noise 1.3–2.6% vs 80% inter-window heterogeneity;
> w8 = 17.726/17.728/17.721 across three splits; w20 = 1.000 across all six fits) →
> three-leg impossibility certificate (P10 366–1116σ model-free + A1 s_W=1 no-op control +
> the T-B theorem) → a held-out-validated carrier model class. Nobody in the literature
> has delivered the first three links.

**Three load-bearing reasons:** (1) the prosecution's concession (above); (2) the
decoder-prior track neither needs nor deserves the headline (Sivak 16% / dMLE 30.6% and our
numbers are mutually protocol-incomparable; likelihood endpoints have *Quantum* precedent —
Wagner, Quantum 6, 809 passed as pure theory with zero data; arXiv:2512.10814's endpoint is
held-out likelihood); (3) K2 is an uplift, not a cap (C0 only kills static non-unital
carriers in the surface BULK; multi-lag R_k on the surface is K2 self-assessed
(a, claimable); the footprint theorem itself is new content; surface replication belongs to
paper 2 and is never a submission gate).

## Surviving claim architecture (mandatory headline order)

1. **Headline: the bunching chain** (spectrum + certificate + carrier model class —
   located, replication-stable, identity-exact);
2. **Support: the likelihood end** — "twin ≥ the budget-feasible optimum of the pij family,
   located" (+56/+44 nats vs SI1000 reported honestly but self-labeled ~80–125%
   detector-marginal — "the cheap part");
3. **Rearguard: the decode-end honest cost accounting** + the A3c/G5 mechanistic claims
   (whatever M4's sign);
4. The miss ledger presented as "falsifiable methodology" (the P7→A2 dissection yielding a
   craft rule is an exhibit, not a stain);
5. The scope sentence quotes the K2 theorem verbatim for the rep-code/surface boundary
   (finished sentences exist in the adjudication).

## Required additions for submission (RA)

| # | Addition | Objection it flips | Effort |
|---|---|---|---|
| RA-1 | Land M4, scored against the registration, **reported whatever the sign** (S10 / reverse-trap protects null results) | "no decode end" | running (WSL session) |
| RA-2 | **Per-sample re-calibrated pij NLL control** (01–04 / 05–09) | the drift-generalization hole (the advocate's only conceded item) | ~a day, machinery exists |
| RA-3 | **One registered attribution-or-exclusion test** (burst flag + transient + dual-basis independence already measured) | McEwen "already attributed and mitigated" | ~a day |
| RA-4 | Protocol-tagged context-bar table + mandatory headline order (see the upgraded "Path 3") | "entering the benchmark from below" | writing-layer |
| RA-5 | **Full-code four-way NLL** (new; see Path 2) | brings Google's own optimized prior into the same protocol | ~a day + registration addendum |

**Enhancements** (not gates): the dMLE mid-scale bracket (= the redirected Path 1, highest-
priority enhancement; r≈101 short windows, multiple repeats, register-then-run), rep-record
multi-lag R_k, (optional) the reverse bridge — the twin run on dMLE's instance protocol.

## Four legal-comparison construction paths (owner-confirmed direction, 2026-06-11)

Requirements: same data, same split, same decoder, same baseline construction, same metric
conventions.

1. **dMLE same-protocol head-to-head → MID-SCALE BRACKET** (owner redirect 2026-06-12; the
   M4 A4 arm closes as its registered documented-drop — all three of their fitting engines
   measured out: the PlanarNet n² law (≈51 GiB for a single shot), the exact path's own
   ≥15-detector gate, the TN search-stage memory lottery (S ∈ {4011, 126, 63, 17.32} across
   four runs; any safe budget buys 2–4 trials) + a fit protocol measuring ≈8.6 days/fit even
   at r=101; full dossier `outputs/m4_a4_dmle_attempt_dossier.md`). Replacement: **register
   a bracket BOTH methods can run — d′=5 × r≈101 short windows** (m=408; our probes
   certified their TN path viable there: search 672 s passes their own S<30 gate at
   S=15.32, GPU fit step ≈3 s per 100-shot mini). Same data, same train split, same frozen
   pymatching, layer-restricted short-window units; multiple repeats (search-seed lottery +
   fit-init seeds + windows); **registration addendum BEFORE any run** (prediction bands +
   fairness clauses: declared pij warm init, declared NLL-plateau stopping rule as an
   execution constant, per-repeat seed log); sequenced after the M4 close. G9's
   cross-protocol language ban stands.
2. **Full-code four-way NLL** (RA-5): the I-1 zero-event finding kills only the LER end,
   not the NLL end; on the same held-out shots and the same declared composed-marginal
   family, score four-way held-out NLL over {SI1000, self-computed pij, **the shipped RL
   prior**, the twin's seam-composed DEM} — pulling the RL prior that Sivak's team optimized
   for THIS dataset onto the same scale (their home turf, full code). Needs: a registration
   addendum (register-then-run), the family-NLL machinery extended from windows to the full
   code (streaming extension of the M3 machinery), and a fairness footnote (the RL prior was
   optimized for decoding, not likelihood; its status as "the strongest shipped prior for
   this dataset" is uncontested).
3. **Protocol-conversion framework** (RA-4 upgraded into a small methodological
   contribution): 16% / 30.6% / +1.5% are mutually incomparable; we hold the exact
   conversion identities (c(s), ε̂ inversion, the Λ̂ ladder). Deliverable: our results
   reported at multiple working points (d′, T) side by side (showing the near-protocol-
   invariant per-round ρ) + a conversion-context table for published numbers under declared
   assumptions (tagged context, never claims).
4. **Own the benchmark**: neither Sivak nor dMLE shipped a reproducible pipeline on this
   public release; we hold a bit-exact pipeline anchor (0/600,000), frozen seeds/hashes, a
   five-arm protocol, .dem + per-edge-band artifacts, and a console entry — frame it as
   "the first protocol-pinned reproducible decoder-prior benchmark on the Willow rep-code
   release". Future methods that want a legal comparison enter OUR protocol. Zero
   experimental cost; a framing sentence.

**Discipline:** any new comparison in Paths 2/3 (and the Path-1 bracket) writes its
registration addendum (prediction bands + fairness clauses) BEFORE it runs.

## The scooping clock

**Measured in months**: arXiv:2512.10814 (2025-12) already observes, on the same data with
the same metric, the symptom our certificate explains; dMLE has been in press since 2026-02.
Adjudication: **submit within 4–6 weeks of M4 scoring; post the arXiv placeholder as soon as
the RA list lands.**

## The two-paper split (previously confirmed with the owner)

- **Paper 1 (small, first, this file's subject)**: the M1–M4 hardware arc, bunching chain
  in the lead, target *Quantum*. No do(), no carrier, no full footprint theory.
- **Paper 2 (large, later)**: M5 drift + surface windows (L1–L3 gated) + the composed
  carrier + the K2 footprint theorem + the controlled counterfactual loop (the full do()
  arc) + the seam second read. The theory skeleton can be drafted now; the experimental legs
  follow the ADR 0007/0008 sequence.

## Future direction: real-time adaptive-prior / streaming monitor (Paper-2 `predict` capstone)

> Owner question (2026-06-12): can this become real-time, given the model is already built
> and only the live context window is new? Answer: YES at the ms–s adaptive-prior layer (NOT
> the µs decode-loop layer — that is the FPGA-blossom domain, Riverlane/Google; we do not
> compete there and do not need to). This is the natural online-ization of the `predict`
> capability — a recorded future direction, trigger-gated, never a near-term gate.

**Why it is feasible with what we already have.** The expensive object — the CPTP fit
(~10–20 s GPU/window) — is OFFLINE; its product is STRUCTURE (which functionals are
identifiable [the craft rule], where the gauge lives, how wide the bands are). The quantities
a decoder actually consumes at run time are exactly the identified coordinates
(r̂, R̂_k, q̂eff), and every one of them has a FIT-FREE closed-form estimator:
- r̂, q̂eff = streaming pair-count accumulators + the Spitz-class identities (XOR + counters,
  FPGA-friendly, O(1)/shot);
- R̂_k = the seam test already DEMONSTRATED fit-free two-block-marginal readout at exact grade
  on controlled truth (Δ ≤ 5e-8);
- f̂ = r̂·R̂ and the rest are (a)-class closed forms.
So: the offline twin answers "WHAT to measure, HOW, and to how many digits"; the online layer
just counts inside a sliding window.

**Why the time scales match.** Prior updates do not need µs — drift is a seconds/minutes/hours
phenomenon (measured: 43–46 nats/shot/window inter-sample; set1 ships 16 sequential
experiments over 15 h), TLS is minutes, leakage/cosmic-ray bursts are ms-scale EVENTS that
need DETECTION not recalibration (the MAD burst-flag machinery already exists). A ms–s prior
refresh suffices; the DEM-weight update is a log((1−p)/p) recompute + the A3c reweight rule —
already-built machinery.

**The one real physical cost (stated honestly).** Statistical latency. M3 pinned R̂ to
1.3–2.6% with ~10⁵ shots/window; shrinking to ~10³ shots (tens-of-ms-scale streams) degrades
R̂ precision ~×10 → ~15–25% — coarse for fine drift tracking but ample for burst detection
(R̂ jumping 1 → 17). The precision–latency curve is itself a publishable figure.

**Roadmap (≈ M5 + an online `predict` module; mostly already-done legs):**
1. offline per-window identified-coordinate dictionary + fit-free estimator validation —
   LARGELY DONE (A2/A3, the seam R_det readout);
2. streaming estimators with a forgetting factor + change-point/burst detection (MAD flag
   exists);
3. prior-update rule → DEM weights / A3c two-pass parameters (machinery exists);
4. latency–precision trade-off measured — **set1's 15 h of drift data is the purpose-built
   testbed** (the M5 proper);
5. an embedded-feasibility note (counters + a few flops — a natural FPGA side channel).

**Differentiation.** Nobody has published a streaming identifiable-functional prior updater
WITH honest uncertainty bands; Google itself only recalibrates pij between experiments. The
project's identifiability theory answers the question an online system most fears — "is the
quantity you are streaming actually identifiable, or a fiber artifact?" (the P7→A2 lesson,
now load-bearing). This is the sharpest industry-differentiation cell of the toolkit goal.
