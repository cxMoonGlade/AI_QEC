# Deep review — Beverland, Carroll, Cross & Yoder, Fail Fast: Techniques to Probe Rare Events in Quantum Error Correction

> Deep reading note (academic-paper-review format; full read Secs. 1–2 incl. the
> `(H,A,C)` formalism, the failure-spectrum transform Eqs. 1–2, the onset-weight
> definition, and the three techniques' overviews; Secs. 3–6 + appendices at the
> structure/result level). **Relevance to the twin** centerpiece.

## Metadata
- **Authors.** Michael E. Beverland, Malcolm Carroll, Andrew W. Cross, Theodore J. Yoder (IBM Quantum).
- **Venue / status.** arXiv:2511.15177 (Nov 2025).
- **Domain / type.** QEC / fault tolerance; **methods** (rare-event estimation + extrapolation), applied to qLDPC (bivariate bicycle) codes.

## Executive summary
Useful logical qubits target logical error rates `P(q)~10^{-12}` — far below what **direct Monte-Carlo** can reach. The paper characterizes the **rare-event regime** of a QEC system across **all** physical error rates `q` using three complementary techniques, organized around the **failure spectrum** `f(w)` = the fraction of weight-`w` fault bitstrings that cause the decoder to fail. A QEC system is `(H,A,C)`: check matrix `H∈F_2^{M×N}`, **action (logical) matrix `A∈F_2^{K×N}`**, decoder `C`; a fault `e` gives syndrome `σ=He`, the decoder returns `c=C(σ)`, and it **succeeds iff `Ac=Ae`**. The logical error rate is a **binomial transform of the failure spectrum**:
> **`P(q)=T{f}(q)=Σ_{w=0}^N f(w)·C(N,w)·q^w(1−q)^{N−w}`** (Eqs. 1–2) — `f(w)` *completely specifies* `P(q)`.

In the low-`q` limit `P(q)≈f(w_0)q^{w_0}`, dominated by the **onset weight** `w_0` (smallest failing weight; `w_0=⌈D/2⌉` for a min-weight decoder, `D` = the distance, which can differ from the code distance `d`). The three techniques: **(I) a failure-spectrum ansatz** — `f(w)` empirically varies *smoothly* and behaves *similarly across all QEC systems*, so a low-parameter closed form (the "min-fail enclosure model," Sec. 3.1) calibrated on accessible `q` predicts `P(q)` everywhere; **(II) min-weight analysis** — compute/bound the min-weight decoder onset `f*(w_0*)` (any decoder has `w_0≤w_0*`, `f(w_0)≥f*(w_0*)`), quantifying the gain available from a better decoder; **(III) multi-seeded splitting** — generalize Metropolis splitting/importance-sampling to qLDPC by seeding chains at high `q` (MC-feasible) with *multiple* typical failing configurations, then re-seeding lower-`q` chains, addressing the ergodicity (disconnected failing-config space) and mixing-time limitations of single-seed splitting. Circuit (non-uniform) noise is handled by an **expanded representation** (replicate each fault's column `m_j ∝` its probability). Applied to distance-6/12/18 **bivariate bicycle codes** under bit-flip + circuit noise with the **Relay decoder**, the techniques agree and predict `P(q)` deep into the rare regime; coherent and Pauli+ noise are flagged as **future work, not handled here**.

For the twin this is the **methodology for the `predict` capability's rare tail**: the failure-spectrum transform `P(q)=T{f}(q)` is the principled below-threshold extrapolator a `do()`→ΔLER claim should ride on (not a sampled ratio against the noise floor); the `(H,A,C)`/"fail iff `Ac=Ae`" formalism is the frozen-decoder ΔLER substrate (`A` here = the twin's DEM parity/action map); and the explicit absence of coherent noise marks the twin's wedge — whether the smooth failure-spectrum ansatz survives coherent (non-Pauli) tails is open.

## Contributions (claim → evidence → strength)
- **C1. Failure-spectrum formalism `P(q)=T{f}(q)` (Eqs. 1–2).** `f(w)` fully specifies `P(q)`; low-`q` ⇒ `f(w_0)q^{w_0}`. *Strength: strong — the unifying object.*
- **C2. Technique I — smooth low-parameter ansatz `f_ansatz(w)` predicting `P(q)` across all `q` (Sec. 3).** *Evidence:* empirical smoothness + cross-system similarity; min-fail enclosure model; ansatz-vs-other-formulas comparison (App. A.3). *Strength: strong (the extrapolator).* 
- **C3. Technique II — min-weight onset `f*(w_0*)` computation/bounds in LDPC (Sec. 4).** Min-weight logical-operator identification; bounds the decoder gap. *Strength: strong.*
- **C4. Technique III — multi-seeded splitting for general qLDPC (Sec. 5).** Fixes ergodicity/mixing of single-seed splitting; results on bivariate bicycle codes. *Strength: moderate-strong.*
- **C5. Application: Relay decoder on bivariate bicycle codes at low `P(q)` (Sec. 6).** Supports YSR+25 resource estimates. *Strength: strong (validation).* 

## Method (deep)
- **Formalism.** `(H,A,C)`; fault `e∈F_2^N` w.p. `q^{|e|}(1−q)^{N−|e|}`; `σ=He`; success iff `Ac=Ae`. **Distance `D`** = min weight of a logical bitstring (`He=0,Ae≠0`), decoder-independent, may differ from code distance `d`. **Onset weight `w_0`** = smallest failing weight; min-weight decoder ⇒ `w_0*=⌈D/2⌉`.
- **Transform.** `T{g}(q)=Σ_w g(w)C(N,w)q^w(1−q)^{N−w}`; `P(q)=T{f}(q)`. Importance sampling = truncate the `w`-sum to `[w_min,w_max]`; fails when `f(w_0)` is tiny (toric `d=21` bit-flip: `f(w_0)≈10^{-18}`) or many `w` contribute.
- **Non-uniform (circuit) noise.** Expanded representation: replicate column `j` `m_j∝` its probability; global `q=p/b`; sampling uniform columns ≡ sampling the compressed model to `O(p²)`.
- **Technique I.** Min-fail enclosure model → closed-form `f_ansatz(w)`; calibrate on accessible `q`, predict all `q`; theoretical + numerical analysis of the fit (App. A.4–A.5).
- **Technique II.** Identify min-weight logicals (toric: `2d` topologically nontrivial paths; weight-`w_0=d/2` failures = half the restrictions, `f(w_0)=d·C(d,d/2)/C(n,d/2)`); LDPC needs new sampling procedures (App. A.6).
- **Technique III.** Metropolis splitting (Ben76, BV13) at a sequence of `q`; multi-seed with several failing configs at high `q`; re-seed lower `q`; X/Z handled separately (App. A.1).

## Methodology assessment
| Criterion | 1–5 | Assessment |
|---|---|---|
| Soundness | **4** | The transform `P(q)=T{f}(q)` is exact; the ansatz is *empirical* (smoothness assumption); min-weight bounds rigorous. |
| Novelty | **4** | Failure-spectrum ansatz + multi-seeded splitting for general qLDPC + min-weight onset bounds — a coherent, useful toolkit, not a single breakthrough. |
| Reproducibility | **4** | Formalism explicit; ansatz + algorithms described; applied to named codes/decoder; appendices give fitting + sampling detail. |
| Experimental design | **4** | Three independent techniques cross-validated (agreement strengthens confidence); multiple distances + noise models. |
| Statistical rigor | **4** | Error bars on sampled `f(w)`; the extrapolation rests on the ansatz validity (the main caveat). |
| Scalability | **4** | Reaches `P(q)~10^{-20}` regimes inaccessible to direct MC; multi-seeded splitting still has unknown mixing time for some large codes. |

## Strengths
- **S1 — the failure spectrum as the unifying object (Eqs. 1–2).** Reducing "LER at all `q`" to one weight-indexed function `f(w)` (binomial-transformed to `P(q)`) is clean, exact, and decoder-faithful — the right abstraction for below-threshold extrapolation.
- **S2 — three independent, cross-validating techniques.** Ansatz fit, min-weight bound, and splitting attack the rare regime from different directions; their *agreement* is the evidence (Fig. 1), which is more convincing than any single extrapolation.
- **S3 — honest about the leading-term structure.** Tying the low-`q` LER to `f(w_0)q^{w_0}` and the onset weight `w_0=⌈D/2⌉` makes explicit *which* rare events dominate and *where* a better decoder can help (Technique II) — directly actionable.

## Weaknesses / limitations
- **W1 — the ansatz is empirical, and coherent/Pauli+ noise is explicitly unhandled.** `f_ansatz` rests on observed smoothness across *Pauli/stochastic* systems; coherent noise (non-Pauli tails) is named as future work (MOH+25). Its validity off the Pauli slice is untested — exactly the twin's regime.
- **W2 — splitting's mixing time is uncontrolled.** Multi-seeded splitting mitigates but does not solve ergodicity/mixing; for some large codes the mixing time is unknown and may grow exponentially.
- **W3 — `predict`/decoder-impact only, not mechanism recovery.** It estimates *logical failure rates* under a frozen decoder; it says nothing about the underlying channel — `predict`, not `recover`/`understand`.

## Relevance to the twin
This is the **`predict`-capability methodology for the rare, below-threshold tail — and the frozen-decoder ΔLER substrate**:
1. **`P(q)=T{f}(q)` is the principled below-threshold extrapolator for `do()`→ΔLER.** The twin's `do()` knob is scored by ΔLER under a frozen decoder; at low physical error rate that ΔLER lives in the rare tail where direct sampling hits the noise floor. The **failure-spectrum fit** is how to extrapolate it honestly — fit `f(w)` from the accessible regime, transform to `P(q)`, and report ΔLER as a *difference of failure-spectrum predictions*, **never a sampled ratio against the noise floor** (the project's explicit metric discipline). This is the concrete machinery behind "report honest bands, never quote a ratio against the noise floor."
2. **`(H,A,C)` / "fail iff `Ac=Ae`" IS the twin's frozen-decoder scoring object.** The action matrix `A` here is the twin's DEM parity/action map (the CLAUDE.md `A` = "DEM parity map, never an assignment matrix"); "succeeds iff `Ac=Ae`" is precisely the logical-failure criterion the twin's `do()`/ΔLER is scored on under frozen-MWPM. This paper is the formal definition of the substrate the twin's `manipulate`/`predict` axes operate over.
3. **Onset weight + min-weight analysis = the structural complement to the twin's exact enumeration.** At small `d` the twin enumerates *all* fault trajectories and computes `f(w)` exactly (so its small-`d` LER *is* `T{f}(q)` with `f` known exactly — a free, exact cross-check of this paper's ansatz). The onset term `f(w_0)q^{w_0}` is the leading-order LER the twin computes directly; this paper is how that accounting scales when full enumeration dies — the bridge from the twin's exact small-`d` teacher to large-`d` `predict`.
4. **Coherent noise unhandled = the twin's wedge (W1).** The ansatz's smoothness is established only on *Pauli/stochastic* systems; coherent-error LER (non-Pauli tails) is open. The twin's coherent `predict` axis below threshold is exactly this untested regime — a concrete contribution opportunity: *test whether the failure-spectrum ansatz survives the twin's coherent teacher*, using the exact small-`d` coherent FLO/enumeration `f(w)` as ground truth.
5. **Multi-seeded splitting = the "generate rare-but-important failure cases" knob.** The twin's stated `predict` knob (produce decoder-stress cases rather than wait for them) is this importance-sampling/splitting machinery; the min-weight-logical enumeration is how to *target* the dominant rare events.

## How to use / trust + open questions
- **Trust:** high as the *rare-event extrapolation methodology* and the *frozen-decoder formalism*; carry W1 (ansatz is Pauli-empirical, coherent untested) and W3 (`predict`, not `recover`).
- **Open questions for the project:** (i) Use the twin's **exact small-`d` `f(w)`** (from full enumeration / FLO) to *test the failure-spectrum ansatz directly* — does the smooth `f_ansatz` reproduce the exact spectrum for stochastic *and* coherent teachers? This both validates the twin's forward and probes W1. (ii) Adopt `P(q)=T{f}(q)` as the **below-threshold ΔLER reporter** for `do()` claims (the honest-band, no-noise-floor-ratio recipe). (iii) Align notation: confirm the twin's `A` (DEM parity map) ≡ this paper's action matrix and that frozen-MWPM `do()`-ΔLER is scored by "fail iff `Ac=Ae`." (iv) Flag coherent-tail extrapolation as a *named open risk* in the `predict` axis until the ansatz is shown to hold off the Pauli slice.
