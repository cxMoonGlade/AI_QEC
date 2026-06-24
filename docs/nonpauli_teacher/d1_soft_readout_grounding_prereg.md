# D1 (soft-readout ③) — IQ-model grounding + pre-registration

**Status:** pre-registration / grounding spec. Theory-first: the soft-readout measurement model,
its grounded parameters (+ the one declared bracket), the constraint ledger, the declared+bounded
simplifications, and the D2–D4 arms/metrics/falsifiable predictions are fixed HERE, before any soft
emission/floor/decoder code runs. Governs the soft phase the way `p7b_estimable_floor.md` governed
the binary floor. Binding: `docs/FAITHFULNESS_PROTOCOL.md` (anti-toy), `docs/METRICS.md`
(epistemic classes + the standard-metric ladder), ADR 0010 (the carrier), `p7_leakage_ler_effect.md`
(⑦, the binary result this extends).

**One line.** ⑦ established that leakage RAISES the optimal LER but that **binary** readout has no
decodable non-Pauli headroom over the best moment-matched Pauli (capped). Soft (analog IQ) readout
keeps the continuous measurement value the hard threshold discards; the `|2⟩`/coherence signature is
visible there. D1 grounds the IQ measurement model and pre-registers the test of whether **soft
unlocks the leakage headroom binary could not** — scored by `%ΔLER` vs the best hard/Pauli decoder
and the gap to the **soft** Bayes floor.

---

## 0. The question (what D2–D4 will answer)

Given the SAME leakage teacher (the d3 qutrit carrier, ADR 0010; ⑦'s arms), does keeping the
continuous IQ readout `μ` instead of the hard bit:

1. **Lower the optimal (Bayes-floor) LER** — `F_soft < F_binary`? (Soft is strictly more information,
   so `F_soft ≤ F_binary` is a theorem; the question is whether the gap is *material* and where it
   comes from — leakage vs ordinary measurement softness.)
2. **Yield decodable soft-ANALOG leakage headroom over the FAIR hard baseline** — not ⑦'s weak
   2-outcome model, but a hard 3-outcome (`|2⟩`-flag) leakage-aware decoder (which already *detects*
   leakage). Is `LER_soft < LER_hard-3` significantly, and — the decisive test — does that advantage
   GROW with the leakage rate above its leak-0 value (the *leakage excess*, §6 D4)? The leakage claim
   rides on the rate-dependence, never on an absolute %ΔLER (which is generic softness — A1).

The headline contribution metric stays the project's: **beat the best Pauli/hard decoder** — and the
"best hard" is the leakage-DETECTING hard-3 baseline, not MWPM-on-2-outcomes
(`project-decoder-gate-and-frontier`: beat the shipped frontier, which already handles leakage). The
soft-vs-hard comparison is decoder-matched and run on the SAME teacher data (apples-to-apples in-sim
ΔLER), never an implied real-hardware SOTA (`alphaqubit` transfer caveat).

---

## 1. Grounding decision — no IQ data in the Google datasets ⇒ literature + a declared bracket

**Checked against the raw artifact (FAITHFULNESS Rule I), not a summary.** All four local Google
releases (rep d29; surface set1; surface set2; 105Q d3/d5/d7) ship, per leaf instance, ONLY Stim
bit-packed `.b8`: `measurements.b8`, `detection_events.b8`, `obs_flips_actual.b8`, plus the two
`circuit_*.stim`, `metadata.json`, `sweep_bits.b8`, and `decoding_results/`. The captured `sample_00`
directory listing (`docs/.datasets/_sources/directory_listings.txt`) confirms the file kit and file
sizes consistent with **1 bit per measurement** (e.g. rep d29 `measurements.b8` = 350.8 MB for
2×10⁷ shots × 57 q × 1000 cycles, bit-packed). No metadata schema carries an IQ/analog key.

> **Conclusion (exact, raw-artifact-verified):** the public Google data is **hard binary readout
> only — there is no IQ/analog/soft data**. Data-grounding of the IQ model is therefore IMPOSSIBLE
> from our datasets. The honest path is **literature-grounding + a declared bracket** (the handoff's
> anticipated "no" branch). Note AlphaQubit *used* Google soft information internally, but that raw
> IQ was never released; our four datasets do not contain it.

Consequence (epistemic discipline): every soft claim is bounded "**on rich-noise simulation, under a
literature-grounded IQ model with a declared bracket on the one under-determined parameter**." No
real-hardware soft claim is admissible.

---

## 2. The soft-readout measurement model (the IQ likelihood)

We adopt the **encoding-independent conditional-density** abstraction (Pattison 2107.13589 §1.3,
Fig. 2; the field-standard soft model): the projective measurement yields a hidden state `k̄`, then a
classical noisy channel emits a continuous outcome `μ ∼ f^{(k̄)}(μ)`. The decoder/floor consume the
continuous `μ`; hard-thresholding `μ` recovers the binary model.

For our QUTRIT teacher the hidden state per measured qubit is `k̄ ∈ {0,1,2}` (a real measurement
*does* collapse to a level — Miao 2211.04728 truncate-and-resolve confirms `|2⟩` is a distinct
measurement outcome), and the IQ readout is a **per-level Gaussian mixture in the 2-D IQ plane**
(Ali et al. 2403.00706, the DIRECT soft-surface-code precedent, Phys. Rev. Applied 22, 044031 (2024)):

  `f^{(k)}(z) = 𝒩(z; c_k, Σ_k)`,   `k ∈ {0,1,2}`,   `z ∈ ℝ²` the IQ point.   (the soft emission model)

**Dimensionality — grounded, not assumed (Ali et al., verified vs the primary source).** The
`|0⟩`/`|1⟩` response is symmetric about the inter-centroid axis, so it projects onto a 1-D discriminant
`μ = z·ê` with **no information loss**; but `|2⟩` sits OFF that axis (its dispersive shift `χ₂` is
independent of `χ₀,χ₁`, not a linear extrapolation), breaking the symmetry, so `|2⟩` must be carried
in the **full 2-D** response (Ali et al., verbatim: "if higher excited states such as `|2⟩` are
considered, the symmetry in IQ space breaks, and we consider the full two-dimensional measurement
response in classification"). We therefore model `|0⟩`/`|1⟩` in 1-D (lossless) and `|2⟩` in 2-D —
exactly Ali et al.'s construction. **The off-axis `|2⟩` component is the leakage information the 1-D
hard discriminator discards and soft readout recovers** — the physical crux of the soft headroom.

### 2.1 The `|0⟩`/`|1⟩` blobs — GROUNDED (Pattison §1.3; Varbanov/AlphaQubit §3.2)

Symmetric Gaussian: `μ_0 = +1`, `μ_1 = −1`, shared width `σ` (means normalized to ±1). The single
free scalar is the SNR `= |μ_0−μ_1|/(2σ) = 1/σ`, tied to the single-shot assignment error by the
field-standard relation

  `p_m = ½ erfc(SNR/√2)`   (Varbanov §3.2; equivalently Pattison's `p_{M,soft}` from the `𝒩(±1,σ²)`
  overlap).

`p_m` (hence `σ`) is grounded to real surface-code-device readout error — a literature range, swept
(not pinned): see §3.1. Ali et al. 2403.00706 confirm this `|0⟩`/`|1⟩` symmetry and its
information-lossless 1-D projection on a real d3 device (the 2-D structure matters only for `|2⟩`,
§2.2). This half of the model is on solid, citable ground.

### 2.2 The `|2⟩` blob — the UNDER-DETERMINED, toy-risk parameter ⇒ a declared bracket

`|2⟩` lands at its own 2-D IQ centroid `c₂` (covariance `Σ₂`) set by its distinct dispersive shift
`χ₂`, **off the `|0⟩→|1⟩` discriminant axis** (Ali et al. 2403.00706; Chalmers 2208.05879 — §3.2).
`|2⟩` IS resolvable in principle (Miao Fig. S1: "a calibrated readout pulse distinguishes the four
lowest levels"), but **no source gives a single physical `c₂` for our (sim) device** — it is
device-, readout-pulse-, and frequency-specific (Chen 2208.05879 Fig. 4a: the blobs move on circular
trajectories as the readout frequency varies). Per FAITHFULNESS Rule II.6 (underdetermined ⇒ bracket,
don't freeze), `c₂` is a **declared bracket**, never a pinned constant. This is THE #1 soft toy-risk (handoff): "a too-separated `|2⟩`
blob hands the answer / fakes the headroom."

**The anti-toy anchor — what it DOES and does NOT bound (corrected after review).** The anchor below
binds the soft model's hard-threshold projection to ⑦'s binary model — a genuine **hard-CONSISTENCY**
constraint (the soft model cannot contradict the validated binary result). It does **NOT** by itself
bound the headroom: it pins the ON-AXIS projection of `c₂` (what the hard discriminator sees) and
leaves the OFF-AXIS component (what soft sees, the headroom driver) FREE. So the anti-fake-headroom
guard is NOT the anchor — it is the §3.2 `P(2→2)` cap + L-soft-3 + **the `P(2→2)`→geometry map below**.
Stating it plainly so no builder trusts the anchor to do a job it cannot. The soft model must reduce,
under hard-thresholding, to the BINARY leaked-readout model ⑦ used. In that model
(`audit/floor_backend.py:_povm_diag_weight_batched`) a leaked qubit contributes a syndrome-parity
factor `d2`, with arm A/C `d2 = 1 − 2b`, B1 `+1`, B2 `−1`; `b ∈ [0,1]` is the swept leaked-readout
bias = P(a leaked qubit reads as the "1"/`−1`-parity outcome). The hard threshold on the soft `|2⟩`
blob projects to exactly this:

  `β₁ ≡ P(threshold says "1" | k̄=2) = ∫_{decide-1} f^{(2)}(μ) dμ`,   and the hardened model is
  `d2 = β₀ − β₁ = 1 − 2β₁`.   ⟹ **consistency requires `β₁ = b`** (arm A) / the B1,B2 extremes.

So the soft model is NOT free at the threshold: its `|2⟩` hard-projection is **pinned to ⑦'s `b`
bracket**. The genuinely free, bracketed quantity is the `|2⟩` **2-D position relative to `|1⟩` at
fixed `β₁`** — *where the `|2⟩` blob sits in the IQ plane*, which the 1-D hard discriminator cannot
see but the analog `z` can. Concretely: the 1-D threshold sees only `c₂`'s projection onto the
discriminant axis, and that projection sets `β₁ = b`; the **OFF-AXIS component of `c₂`** (its 2-D
separation `|c₂−c₁|` from the `|1⟩` centroid) is free along the `b`-isocontour — and that off-axis
component is exactly the leakage signal soft recovers and the hard bit discards.

**Two measurement points, one anchor.** The binary model treats a leaked readout at BOTH measured
locations: (i) the per-round ancilla **syndrome** POVM (`d2 = 1−2b`, arm A) and (ii) the **terminal
data** logical readout (`_logical_sector_traces_batched`'s "leaked logical support split evenly" —
the binary neutral default, i.e. a leaked data qubit contributes ½/½ to the logical-parity sectors).
The soft model refines BOTH: the analog `μ` of a leaked ancilla refines `d2`, and the analog `μ` of a
leaked data qubit refines the "split-evenly" default. The consistency anchor (L-soft-1) therefore
binds the `|2⟩` blob's hard-projection at BOTH points (to `b` and to the ½/½ default respectively),
and the §2.2 bracket on `c₂` applies to both (under the homogeneous-readout simplification S6). NB: the
½/½ data-readout default is the WEAKEST hard baseline; the FAIR hard comparator is the hard-3
leakage-flag decoder (§6 D4) — soft must be scored over that, not over ½/½.

The toy ("fake headroom") is the choice of an unphysically large `|c₂−c₁|` (|2⟩ far from |1⟩, so
leakage is trivially visible in `z`). The honest bracket therefore runs, parameterized by the
**correct-`|2⟩`-ID = `P(2→2)`** (the field-standard distinguishability handle from the §3.2 assignment
matrices):

- **(a) worst-case-for-soft endpoint:** `c₂ → c₁` (|2⟩ indistinguishable from |1⟩ in IQ; `P(2→2)`
  ~0.5–0.7, a qubit-only-optimized readout with no `|2⟩` tone). Soft carries NO extra leakage
  information here — the conservative floor on the headroom. (Matching `b` here may need a small
  threshold offset; declared in D2.)
- **(b) realistic-max endpoint:** the largest `|2⟩` separation the 3-state dispersive-readout
  literature actually reports — correct-`|2⟩`-ID **capped at ~0.87–0.94** (NOT a free large number;
  §3.2). The most-favourable-for-soft *physical* case; anything beyond (near-perfect `|2⟩` separation)
  is flagged UNPHYSICAL and excluded — the literature shows adding a `|2⟩` class ~2.4×s the
  assignment error (Krinner 0.9%→2.2%), never makes `|2⟩` trivially separable.
- **(c) representative middle:** correct-`|2⟩`-ID ~0.85–0.90, with the `|2⟩→|0⟩` vs `|2⟩→|1⟩`
  confusion DIRECTION itself swept (scheme-dependent — §3.2; maps onto the binary arms A/B1/B2).

**D4 MUST report `headroom_soft` as a function of the `|2⟩` separation (`P(2→2)`) across the full
bracket** (the mandatory sensitivity sweep), and the conclusion must be stated as it depends on the
bracket — never collapsed to one endpoint. The headroom→0 limit as `c₂→c₁` is a registered positive
control (§4 L-soft-3).

**`P(2→2)` does not fix the headroom — the residual-geometry freedom (review fix A2/F2).** Fixing
`P(2→2)` constrains a discriminability summary, NOT the 2-D geometry: two `|2⟩` placements with the
SAME `P(2→2)` (and the same on-axis projection `β₁=b`) can have different OFF-AXIS separations from
`c₁`, hence different soft headroom. The literature gives `P(2→2)` (assignment matrices) but NOT the
off-axis σ-ratio (the genuine gap, §3.2). Therefore D4 sweeps a SECOND axis at fixed `P(2→2)`: the
on-axis/off-axis decomposition of `c₂` (equivalently, the angle of `c₂` off the discriminant axis),
bracketed from "minimal off-axis" (collinear, `|2⟩` shelved beyond `|1⟩`) to the maximal off-axis
consistent with `P(2→2)`. The headline number is reported over BOTH axes; if it is sensitive to the
off-axis angle at fixed `P(2→2)`, that sensitivity is the honest uncertainty band, not hidden.

### 2.3 The soft edge weight (decode side, Pattison Eqs. 6–7) — independent closed-form check

For symmetric-Gaussian `|0⟩`/`|1⟩` the Bayes-optimal soft edge weight is `w(e) = −log L(μ) =
(2/σ²)|μ|` (Pattison §3.2 Gaussian closed form; confidence `|μ|` ↦ linear edge cost). This is a
*derived* (Bayes, Lemma 4.3), not heuristic, weight; we reuse it as the soft-MWPM baseline (D4) and
as an independent analytic check on our soft floor in the no-leakage symmetric limit (§4 L-soft-2).
The general `|2⟩`-aware weight uses the full 3-component likelihood ratio.

### 2.4 Asymmetry / T1-during-readout (declared simplification, §5)

Real IQ blobs are asymmetric (relaxation during the finite ~µs readout biases `|1⟩` toward `|0⟩`;
Pattison App. A, the amplitude-damping channel; Varbanov "open: asymmetric/non-Gaussian"). The
symmetric-Gaussian baseline is the first rung; the asymmetric (Pattison Eqs. 40–41) emitter is a
declared, bounded extension (§5-S4). Note Pattison's amplitude damping is **T1 on the readout signal,
not `|2⟩` leakage** (Pattison W1) — it does not substitute for the `|2⟩` blob.

---

## 3. Grounded parameters + the `|2⟩` bracket (numbers)

> **Provenance discipline:** every number below is data > literature > declared-bracket, with its
> citation. §3.2 is FILLED and primary-source-verified: a focused un-led research pass gathered the
> 3-state transmon dispersive-readout literature, and the orchestrator verified the load-bearing
> numbers against the raw papers (Ali et al. dimensionality + 6.8%/5.0% vs the full text; Krinner
> 2.2% 3-state vs the source) before they entered this section — no figure-read is treated as exact.

### 3.1 `|0⟩`/`|1⟩` readout (the `σ`/`p_m` sweep) — literature-grounded

Single-shot 2-state assignment error for surface-code-class superconducting devices is ~0.4–2.5%,
mean ~1%: the QEC-relevant anchor is **Krinner 2112.03708 (ETH Surface-17, a real d3 surface code):
mean 0.9%, per-qubit 0.4–2.3%** (text, high conf); corroborated by Ali et al. 2403.00706 (device
readout 1.2%), Google Table S1 readout+reset 1×10⁻² [Miao 2211.04728], Varbanov ancilla `p^a_m`=1%
(data `p^d_m`=0.1%) [2307.03280]. (Google Willow/Sycamore per-component numbers are plot-only / not
text-extractable — Krinner/Ali anchor `σ`.) We sweep `p_m ∈ {0.3%, 1%, 2%}`, representative
`p_m = 1%`. With the convention `SNR ≡ |μ₀−μ₁|/2σ = 1/σ` (Varbanov/AlphaQubit), `SNR = Φ⁻¹(1−p_m)`
gives **SNR ≈ 2.75, 2.33, 2.05** (`σ ≈ 0.36, 0.43, 0.49`); equivalently `μ`-separation
`2/σ ≈ 5.5, 4.7, 4.1 σ` in the full-separation convention. **(class (c) gate values for the sweep;
the relation `p_m=½erfc(SNR/√2)` is (a) exact.)** Rationale for the sweep: Varbanov/AlphaQubit show
the soft benefit is negligible when readout is clean (`p^a_m ≲ 0.1%`) and grows with `p_m` — so the
sweep is load-bearing, not cosmetic.

### 3.2 The `|2⟩` IQ bracket — literature-grounded (verified vs the primary sources)

**Geometry (high confidence).** `|2⟩` is **2-D-distinct / off the `|0⟩→|1⟩` axis** — `χ₂` is an
independent dispersive shift, so the three states form a triangle, not a line. Primary: Ali et al.
2403.00706 (the symmetry-breaking statement, §2.0, verified verbatim); Chen/Bylander 2208.05879
Fig. 4a (blobs move on circular trajectories vs readout frequency); IBM 2307.13504 Fig. 4a. The
qubit-optimal readout frequency does NOT maximize `|1⟩–|2⟩` separation, so `|1⟩↔|2⟩` is the tightest
(worst-confused) pair. **No source reports a clean dimensionless `|1⟩–|2⟩`-vs-`|0⟩–|1⟩` separation
ratio in σ — a genuine gap; the bracket is parameterized by the reported `P(2→2)` instead.**

**3-state assignment matrices (the bracket data).**
- Chen/Bylander 2208.05879 (Chalmers transmon, Qubit 2, 140 ns, NO parametric amp; Fig. 4b — figure-
  read ~1%, `|2̃⟩` bundles `|2⟩+|3⟩` so `P(2→2)` is slightly optimistic): `P(2→2)≈0.87`, `P(2→0)≈0.09`,
  `P(2→1)≈0.04`. Aggregate: 2-state 99.5%, 3-state 96.9% (text, high conf). `P(2→0) > P(2→1)` here —
  T1-during-readout + shelving push `|2⟩→|1⟩→|0⟩`.
- Krinner 2112.03708 (ETH **Surface-17, a real d3 surface code** — most QEC-relevant; text, high
  conf): 2-state mean **0.9%** (0.4–2.3%); 3-state mean **2.2%** (0.9–5.9%). ⟹ **adding the `|2⟩`
  class ~2.4×s the assignment error** — `|2⟩` dominates 3-state confusion.
- HMM / multi-level (2006.00109 / 2405.08982): correct-ID `|0⟩`>99%, `|1⟩`>94%, `|2⟩`>93%
  (abstract-level, medium conf; full off-diagonals not extracted).

**The cap (high confidence).** Realistic correct-`|2⟩`-ID tops out ~**0.87–0.94**; the literature does
NOT show `|2⟩` trivially/perfectly separable on QEC devices (Krinner: the `|2⟩` class ~doubles the
error). A model with near-perfect `|2⟩` separation is UNPHYSICAL and excluded (the toy guard).

**Confusion direction is scheme-dependent (a swept knob).** Dispersive-triangle / short readout →
`|2⟩` confuses toward `|1⟩`; shelving / long readout / T1 → toward `|0⟩` (Chalmers `P(2→0)>P(2→1)`).
The binary arms A/B1/B2 (`d2=1−2b`/`+1`/`−1`) span this; D4 sweeps it (it is NOT pinned).

**The bracket (the registered D2–D4 inputs):**

| endpoint | `P(2→2)` (correct-`|2⟩`-ID) | regime | role |
|---|---|---|---|
| (a) worst-for-soft | ~0.5–0.7 | qubit-only readout, `c₂≈c₁` | conservative floor; headroom→0 control |
| (c) representative | ~0.85–0.90 | typical 3-state readout, `P(2→0)≈P(2→1)` swept | the headline cell |
| (b) realistic-max | ~0.87–0.94 (cap) | dedicated `|2⟩` tone / shelving | most-favourable physical; beyond = excluded |

`|0⟩`/`|1⟩` `σ` from §3.1 (`p_m`≈1% representative). All endpoints class **declared-bracket**; the
`P(2→2)` values are **literature-grounded** (citations above) at the stated confidence, with two
flagged gaps (no σ-ratio; Google per-component plot-only).

**Provenance (FAITHFULNESS Rule I).** The load-bearing dimensionality claim (`|2⟩` 2-D) and the
6.8%/5.0% headroom envelope (§6) were verified by the orchestrator against the Ali et al. PRIMARY
source (arXiv:2403.00706v1 full text + PRApplied 22, 044031 abstract); the assignment-matrix numbers
are the cited figures/tables at stated confidence. A focused un-led research agent gathered the
candidates; **no number entered this section without a primary-source check** (anti-rubber-stamp).
[Follow-up: a full reading note for Ali et al. 2403.00706 — the soft-surface-code precedent — is
warranted in `docs/papers/reading_notes/` (normal docs flow).]

### 3.3 The leakage rates (already grounded; ⑦/ADR 0010) — carried forward unchanged

Per-cycle leakage generation ~5×10⁻³, lifetime ~4.4 cycles, intrinsic ~4×10⁻³/round [Miao]; the WG
`(L_1,L_2,C_L)` parameterization with the exact-qutrit carrier (no coherence discarded). The soft
phase sweeps the SAME WG leak rate ⑦ used (so `headroom_soft`-vs-rate is the leakage signature).

---

## 4. Constraint ledger (physical/statistical invariants + a falsifying test each — BEFORE building)

Each test must FAIL LOUDLY on a broken input (confirmed by a positive control), per FAITHFULNESS
Rule II. Appended to the standing ledger.

| # | Invariant | Falsifying test (must trip on broken input) |
|---|-----------|---------------------------------------------|
| **L-soft-1 (hardening consistency)** | EXACT leg (`p_m→0`): hard-thresholding the soft emission reproduces ⑦'s binary model exactly — `|0⟩/|1⟩`→`±1` with no computational-subspace flip, the `|2⟩` blob projects to `β₁ = b` (arm A/C `d2=1−2b`). FINITE-`p_m` leg: ⑦'s binary POVM has NO `|0⟩/|1⟩` assignment error (only `|2⟩` carries `b` — `qutrit_dm.py` L512–515), so at finite `p_m` the hardened soft model must match a `p_m`-GENERALIZED binary model (computational bit-flip at `p_m` + the `b`-leak POVM), NOT ⑦'s `p_m=0` `P(s)`. | At `p_m→0`: threshold the soft teacher's `z`, rebuild detectors, compare to ⑦'s DM-exact `P(s)` at matched `b`: mismatch > MC band ⇒ FAIL (a wrong `c₂↔b` map trips it). At finite `p_m`: compare to the `p_m`-generalized binary `P(s)`; comparing to the `p_m=0` reference would FALSELY fail a correct emitter — the reference is the load-bearing part. |
| **L-soft-2 (Bayes-weight closed form)** | In the no-leakage symmetric-Gaussian limit the soft floor + soft-MWPM weight equal Pattison's `(2/σ²)|μ|` analytic form (an INDEPENDENT closed form, not our engine). | Compute the soft edge weight from our likelihood vs `(2/σ²)|μ|` over a μ-grid: deviation > 1e-9 ⇒ FAIL. |
| **L-soft-3 (headroom positive control / no-fake-headroom)** | As `c₂ → c₁` (|2⟩ indistinguishable from |1⟩ in IQ), the soft leakage headroom → 0 (soft cannot see what is not in `z`); as `c₂` separates, it rises monotonically. | Sweep `c₂` across the bracket; if `headroom_soft` is NONZERO at `c₂=c₁` or NON-monotone in separation ⇒ FAIL (a leak in the floor/decoder fabricating headroom). |
| **L-soft-4 (no-coherence-smuggling; corrected — the prior info–disturbance form was VACUOUS)** | Because the soft `μ` is a classical readout of the ALREADY-COLLAPSED level `k̄` (D2: "dynamics unchanged"), the post-measurement state is identical to the binary instrument BY CONSTRUCTION — so a backaction-comparison test is `X==X` and cannot fail (the prior L-soft-4). The REAL invariant: the soft likelihood `f^{(k̄)}` depends on `k̄` ONLY through the post-collapse level — it carries level-population info about `|2⟩`, NOT coherence (consistent with "coherence not identifiable from binary syndromes"). | Wire `μ` to a PRE-collapse amplitude / an off-diagonal (coherence) term and assert the soft floor/decoder output CHANGES (it must NOT for the registered model) ⇒ a coherence-smuggling emitter trips. (If a coherence-bearing weak-measurement readout is ever intended, it contradicts D2's "dynamics unchanged" and needs its own grounding + a real backaction test.) |
| **L-soft-5 (soft floor ≤ binary floor — a MONOTONICITY tripwire, not an accuracy check)** | `F_soft ≤ F_binary` at matched conditions (DPI: hard-thresholding is a coarsening of `z`, so the Bayes risk cannot rise); equality iff `z` carries no extra info. NOTE this is partly tautological given L-soft-1 (the binary model IS the hard projection of the soft one) and it catches only an UP-biased soft floor — it is BLIND to the dangerous DOWN-bias (the headroom-inflating direction); that is L-soft-9's job. | If `F_soft > F_binary + MC-band` ⇒ FAIL (catches an up-biased / non-monotone estimator). Reclassified from "independent ground truth" to "monotonicity sanity tripwire." |
| **L-soft-6 (CPTP / probability semantics)** | The soft-augmented forward stays CPTP (residual < 1e-12); the soft `(z,f)` joint normalizes: `∫ Σ_f P(z,f) dz = 1`, `P(z,f) ≥ 0`. | CPTP leg: explicit Kraus residual (`floor_backend.cptp_residual`), CAN fail. Normalization leg: test the NUMERICAL/quadrature/IS-normalized estimate of `∫ Σ_f P̂(z,f) dz` (which CAN drift), NOT the analytic Gaussian mixture (normalized by construction = vacuous). |
| **L-soft-7 (floor convergence, FAITHFULNESS #7)** | The soft-floor estimator does NOT drift with N (no down-biased plug-in); the continuous-record estimator is convergence-checked against the DM oracle at d3-subregister small R. | `F̂_soft(N)` slope > 0 within SE ⇒ not converged ⇒ STOP; an in-sample soft plug-in must be shown to rise as the positive control. |
| **L-soft-8 (DD-echo / frame, FAITHFULNESS #1+#3)** | Every physical gate the real circuit applies stays in the soft forward, incl. the per-round transversal X/Y DD echoes (decisive for leakage; dropping them over-states `|2⟩` up to 504×) and the post-M Y echo's `CY rec[..]` decoder frame at R≥2. | Drop the echoes ⇒ leakage inflates vs the d3 DM oracle, caught at the soft cert; the seam's frame positive control (`g2_positive_control`) extended to the soft path. |
| **L-soft-9 (soft-floor inner-`k̄` marginalization bias — the ⑦-artifact guard for soft)** | `F_soft` requires marginalizing the hidden hard record `k̄∈{0,1,2}^{R·n_stab}` per sample: `P(z,f)=Σ_{k̄}P(k̄,f)∏f^{(k̄)}(z)`. Plugging a NOISY importance-sampling estimate of `P(z,f)` into the concave `min(·,·)` is **DOWN-biased by Jensen** ⇒ inflates `gap=LER−F` ⇒ FALSE headroom (the exact ⑦ down-bias family; L-soft-7 (outer-N drift) and L-soft-5 (up-bias only) do NOT catch this inner bias). | (i) EXACT enumeration of `k̄` (feasible on the sub-register up to the largest R where `3^{R·n_stab}` enumerates) is the unbiased anchor; the IS estimator must match it within MC-SE. (ii) Inner-IS diagnostic: effective sample size / IS-weight variance at fixed `z`, with a positive control (a deliberately mismatched proposal) that MUST trip. (iii) Bound + report the bias DIRECTION. Full-d3 R≥2 soft floor is PROVISIONAL until (i)–(iii) hold; the verdict is driven by the exact small-R anchor (the p7b §2 fallback). |
| **L-soft-10 (independent `f^{(2)}` ground truth — anti-circular)** | The D3 enumeration anchor and the IS estimator SHARE the emission model `f^{(k)}`, so their agreement certifies the ESTIMATOR, not the faithfulness of the `|2⟩` likelihood `f^{(2)}` itself (lumped-vs-lumped; L-soft-2's `(2/σ²)|μ|` closed form covers ONLY the no-leakage `|0⟩/|1⟩` limit). | An INDEPENDENT check of the `|2⟩` soft likelihood: an analytic 3-Gaussian Bayes-error closed form in a tractable limit (or a from-scratch second implementation sharing no code), applied to a `|2⟩`-bearing case; mismatch ⇒ FAIL. State explicitly that L-soft-2 does NOT cover `f^{(2)}`. |

The independent ground truth for L-soft-1/2/9/10 is, respectively: ⑦'s binary DM-exact distribution
(+ a `p_m`-generalized binary model at finite `p_m`); Pattison's closed-form weight; the exact `k̄`
enumeration on the sub-register; an analytic/from-scratch `f^{(2)}` Bayes-error. L-soft-5 is a
monotonicity TRIPWIRE (not ground truth — corrected). None is a check against the soft engine's own
output in the dangerous (down-bias) direction (anti-circular).

---

## 5. Declared + BOUNDED simplifications (FAITHFULNESS Rule III; unbounded = STOP)

| # | Simplification | Class | Bound / how certified |
|---|----------------|-------|------------------------|
| S1 | **Symmetric Gaussian** `|0⟩`/`|1⟩` blobs (no readout-T1 asymmetry) | (c) baseline | Bounded by re-running the representative cell with Pattison's asymmetric amplitude-damping emitter (Eqs. 40–41) and reporting the headroom delta; if the asymmetric headroom differs materially it is promoted, not assumed away. |
| S2 | **Single `|2⟩` level** (no `|3⟩+`) in the readout blob | (a)/(b) | WG/Miao: `|2⟩` dominates; `|3⟩` enters only via transport resonances. The carrier is qutrit (ADR 0010); `|3⟩` is out of the carrier's scope and declared, not silently dropped. Bounded by the WG coherence bound `C_L ≤ 2√(L(1−L))` for any discarded coherence (here zero — the carrier is exact qutrit). |
| S3 | **IQ dimensionality** — `|0⟩`/`|1⟩` in 1-D, `|2⟩` in full 2-D | (a)/(b) grounded | Ali et al. 2403.00706 establish (on a real d3 device) that the `|0⟩`/`|1⟩` 1-D projection is information-lossless **UNDER THE SYMMETRY ASSUMPTION** (Ali states it conditionally: "*Assuming* the IQ responses … are symmetric … the projection does not result in information loss"), and that `|2⟩` requires the full 2-D response — we follow exactly. Residual (review fix F4): the 1-D `|0⟩/|1⟩` projection IS lossy to the extent the blobs are asymmetric (real T1-during-readout), so the loss is O(asymmetry), NOT literally zero — bounded by the S1 asymmetric re-run; plus the per-blob Gaussian shape (S1). The 2-D `|2⟩` is the faithful choice the verified Ali grounding (§2.0) upgraded the draft's flagged 1-D simplification to. |
| S4 | **i.i.d. per-measurement readout noise** (no correlated-in-time IQ, no readout crosstalk) | (c) | Declared; the leakage temporal correlation comes from the state (the `|2⟩` persistence), NOT the readout noise. A correlated-readout extension is out of D1–D4 scope; flagged. |
| S5 | **Threshold at the `|0⟩`/`|1⟩` midpoint** for the hardening map | (c) | The ML threshold (Pattison Eq. 1); at the worst-case bracket endpoint (`μ_2→μ_1`) a small offset to hold `β₁=b` is declared in D2 and reported. |
| S6 | **Homogeneous readout model** (one `(σ, μ_2, σ_2)` IQ model shared across all ancilla + data qubits) | (c) | Real devices have per-qubit readout calibration spread; D1–D4 use a common model (the leakage-headroom question is about the readout *physics*, not per-qubit dispersion). Bounded by re-running the representative cell with per-qubit `σ` drawn from the literature spread (§3.1) and reporting the headroom delta; flagged for promotion if material. |

No simplification here is unbounded. S2's coherence bound is *zero* (exact qutrit carrier) — the one
place the project historically lost faithfulness (the `C_L=0` toy) is structurally absent.

---

## 6. Pre-registration of D2–D4 (arms, metrics, predictions)

### D2 — soft emission (extend the forward to emit IQ) — SCOPE: terminal-soft (user decision 2026-06-22)
**The carrier reality (verified, `mps_forward.py`).** The carrier models ONLY the 9 data qutrits; the
8 ancillas are idealized into a **direct joint-parity POVM** on the data support (`E_s=½(I+(−1)^s Π_q
D_q)`, a leaked data qubit biases it via `d2=1−2b`), and the terminal readout is a **per-data-qubit**
biased-bit POVM. This idealization is exactly what keeps the **3^9 DM oracle feasible** (the cert
anchor). Consequence: a leaked qubit's analog LEVEL is directly readable only at the **terminal data
readout** (per-qubit); the per-round syndrome is a joint parity with no per-qubit level.
**Scope (terminal-soft).** Soft emission is at the **terminal per-data-qubit readout**: realize the
data qubit's level `k̄∈{0,1,2}` (a 3-outcome projective measurement = the `hard-3` baseline), then
emit a continuous `z ∼ f^{(k̄)}(z)` (1-D for `|0⟩/|1⟩`, 2-D for `|2⟩`, §2). Thresholding `z` (or
collapsing the level to the biased bit) recovers ⑦'s `hard-2`. The per-round SYNDROME stays the HARD
parity (the per-round data-leakage effect is already in it via `d2`); it carries no per-qubit level, so
no soft-leakage there. The forward dynamics are unchanged (additive output at the terminal).
**Deferred + flagged (PROVISIONAL, user decision):** the per-round soft-*syndrome* leakage benefit
(Ali/Varbanov's main mechanism) needs EXPLICIT ANCILLA qutrits → 3^17 DM (≈267 PB) → NO certification
oracle. It is a separate, oracle-free, provisional extension — NOT D2. (A 2-outcome soft-parity
syndrome = generic `|0⟩/|1⟩` confidence, which cancels in the leakage-excess metric, is also out of D2.)
**Where it plugs in.** The seam (`forward/scalable/seam.py`) gains a soft variant emitting
`(hard syndrome record `R·n_stab` bits, terminal soft `z` `n_data`×IQ, `logical_flip`)` — the hard
detector path stays byte-identical (L-soft-1 is its consistency guard). The forward's
`_terminal_readout` (`mps_forward.py`) is the integration point (replace the biased-bit collapse with
a 3-outcome level draw + soft `z` emission).
**Deliverable + cert:** the terminal soft emitter + L-soft-1 (terminal hardening reproduces ⑦'s
biased-bit terminal `P` at `p_m→0`; the `p_m`-generalized leg at finite `p_m`) + L-soft-6 (CPTP +
numerical normalization) + L-soft-8 (echoes/frame) as `tests/`. GPU-only model compute.

### D3 — soft Bayes floor (the optimal LER under the soft likelihood)
**The object (terminal-soft).** The record is `(hard syndromes s_{1..R}, terminal soft z =
(z_1..z_{n_data}))`. `F_soft = E_{(s,z)}[min(P(f=0|s,z), P(f=1|s,z))]`, with
`P(s,z,f) = Σ_{k̄ ∈ {0,1,2}^{n_data}} P(s, k̄, f) ∏_q f^{(k̄_q)}(z_q)` — the soft terminal record `z`
MARGINALIZES the hidden **terminal data levels** `k̄` (NOT the per-round syndrome, which is hard).
**This is EXACT at d3 (the terminal-soft payoff).** The syndrome path `s` is hard, so — exactly as the
binary floor — Born-branch one `m` (sampling `s`) and re-evolve the other onto the same `s` (the DM
conditional `ρ_{s|m}`); from `ρ_{s|m}` the terminal-level × logical joint `P(k̄, L | s, m)` is read
exactly, and the soft `z` marginalizes over `k̄ ∈ {0,1,2}^{n_data}` (= **3^9 = 19683 at d3 —
ENUMERABLE**). So the d3 soft floor is **exact per sampled syndrome path** — NO inner importance
sampling, NO Jensen down-bias. **L-soft-9's inner-`k̄` risk recedes to d5+** (where `3^{n_data}`
explodes and IS is needed); at d3 it does not bite.
**Design (pre-registered, ≥3 agents + review):** extend the floor backend's terminal read to return
the per-data-qubit level distribution (the `3^{n_data}` terminal-level × logical joint from
`ρ_{s|m}`), then convolve with the soft likelihood `∏_q f^{(k̄_q)}(z_q)` and `min` over `f` — all
exact at d3. The `|2⟩` likelihood `f^{(2)}` still gets an INDEPENDENT closed-form/from-scratch check
(L-soft-10 — the emission model is the one thing the enumeration shares, so certify it separately;
L-soft-2 covers only `|0⟩/|1⟩`). `bayes_floor`'s outer averaging stays backend-agnostic; the soft seam
is the per-level IQ likelihood + the terminal-level read.
**Deliverable + cert:** `F_soft` exact at d3 (matches an independent enumerator, L1-style);
`f^{(2)}` independently checked (L-soft-10); `F_soft ≤ F_binary` monotonicity tripwire (L-soft-5);
`F_soft = F_binary` at `c₂→c₁` AND at SNR→∞ (clean readout) as positive controls. The d5+ inner-IS
estimator + L-soft-9 control is deferred with the explicit-ancilla extension (both PROVISIONAL).

### D4 — soft foils + headroom (does soft unlock what binary couldn't)
**The baseline hierarchy (review fix — gap-hunt + A4) — AT THE TERMINAL data readout (terminal-soft
scope, D2).** A leaked `|2⟩` is a RESOLVABLE discrete outcome (Miao truncate-and-resolve), so the
honest hard baseline is NOT ⑦'s biased-bit. Ladder of the **terminal** readout, weakest→strongest:
- **`hard-2`** = ⑦'s terminal biased-bit (a leaked data qubit reads as a bit with bias `b`; does NOT
  flag leakage) — the weakest baseline.
- **`hard-3`** = a terminal 3-outcome (discrete `|2⟩`-flag) level readout + a leakage-aware
  (erasure-style) decoder — **flags leakage, NO analog**. The FAIR hard baseline.
- **`soft`** = the terminal analog `z` (graded confidence on the `|2⟩`-vs-`|1⟩` ambiguity).

**All three arms share the SAME hard parity syndrome** (terminal-soft scope); the ladder differs ONLY
in the terminal data readout. So the comparison isolates the value of resolving/grading TERMINAL data
leakage — the per-round soft-syndrome channel is out of scope (deferred, D2).

**Y-echo frame (D2-CONFIRMED — builder B, 2026-06-22).** The raw terminal logical flip carries a
DETERMINISTIC post-M-Y-echo offset (it saturates ~1.0 on `|m⟩_L` at R=2 even at leak=0) — a
PRE-EXISTING ⑦ convention (the `parity(bits)⊕m` flip includes the accumulated transversal-Y echoes),
NOT a bug. Two consequences: (i) the soft floor `F_soft` is **INVARIANT** to it (`F=Σ min(P(s,f=0),
P(s,f=1))` is symmetric under a deterministic `f→f⊕const`), so the frame does NOT corrupt the floor;
(ii) every DECODER arm (hard-2/hard-3/soft) MUST apply the **`CY rec[..]` frame correction** (as ⑦'s
foil does) so its predicted flip matches the frame-correct truth — else the LER is garbage. The
L-soft-1 emission check therefore uses the per-qubit terminal **bit marginal** (frame-free), never the
raw saturated flip. (This is the memory-flagged "src seam may need Y-echo frame handling" — now
concretely located at the terminal flip; the D4 foils inherit ⑦'s correction.)

The gap `hard-2→hard-3` is the **leakage-DETECTION** benefit — NOT soft, and essentially already
deployed (Google leakage rejection / DQLR, Miao). The gap `hard-3→soft` is the **genuine soft-ANALOG**
contribution. The headline "soft unlocks leakage" must be carried by the SECOND gap; reporting
soft-over-`hard-2` conflates detection with analog and over-states the contribution.

**Arms (all on the SAME teacher data; frozen, DECODER-MATCHED; the foil discipline):**
- `LER_hard-2` — ⑦'s best moment-matched Pauli-DEM + frozen MWPM on hard-2 syndromes. Also report
  whether the recal foil is DISTINCT from the leak-blind foil PER REGISTER (on small sub-registers ⑦
  found recal==blind ⇒ the "best Pauli" is not exercised there — A4a; the full-d3 recal-vs-blind was
  never measured and must be).
- `LER_hard-3` — hard 3-outcome (`|2⟩`-flag) readout + leakage-aware decoder (the FAIR hard baseline).
- `LER_soft-MWPM` — Pattison soft-MWPM with `−log L` (Pattison Eqs. 6–7 / Ali Eq. 1; `(2/σ²)|μ|` for
  `|0⟩/|1⟩`, the 3-Gaussian 2-D likelihood for `|2⟩`); rank-2 only (Pattison W4).
- `LER_soft-NN` — a soft-defect-input NN (Varbanov §3.2 `P(d|z)`, NOT raw `z`) AND a **hard-NN at
  EQUAL richness** on `hard-3` inputs — so soft-vs-hard isolates INFORMATION, not decoder class
  (A4b: the project's prior TN-MLD-vs-MWPM confound).
- **`LER_leak0`** — every decoder ALSO run at **leakage rate = 0** (the explicit null — fix #1).
- `F_soft`, `F_binary`, `F_hard3` — the floors (D3, ⑦, + the 3-outcome floor).

**Metrics (METRICS.md ladder):**
- `headroom_soft = LER_soft-decoder − F_soft` (gap of the soft decoder to the soft optimum).
- Baseline-hierarchy split: `%ΔLER(hard-2→hard-3)` = the detection benefit (NOT our soft claim);
  **`%ΔLER(hard-3→soft) = (LER_hard-3 − LER_soft)/LER_hard-3`** = the genuine soft-analog contribution
  (decoder-matched).
- **THE HEADLINE = leakage EXCESS (fix #1; A1/A3):**
  `Δ%ΔLER_leak = %ΔLER(hard-3→soft; rate r) − %ΔLER(hard-3→soft; rate 0)` — the soft-analog advantage
  ATTRIBUTABLE to leakage = its excess over the generic-softness value at leak-0. Required: SIGNIFICANT
  and MONOTONE in r. (Soft-over-`hard-2` and the absolute %ΔLER are reported as context, NOT headline.)
- `ΔF_soft = F_binary − F_soft`, reported as `ΔF_soft(r) − ΔF_soft(0)` for the leakage attribution.
- `%ΔLER` form = the Sivak/dMLE relative-reduction convention, applied as Ali et al.'s
  soft-vs-hard-DECODER comparison (not the Sivak prior-vs-prior axis) — cite accordingly.
- Scaling: vs WG leak rate, vs `p_m`, **and the two-axis §2.2 sensitivity — `P(2→2)` AND the off-axis
  decomposition at fixed `P(2→2)`** (mandatory).
**Falsifiable predictions (class (b) bands — a miss is a finding, not a fact). The leakage claim is
carried ENTIRELY by the rate-dependence (pred. 1) and the `c₂→c₁` control (pred. 4); NEVER by matching
an absolute %ΔLER to the literature (which is generic-softness — A1).**
1. **Leakage EXCESS `Δ%ΔLER_leak > 0`, SIGNIFICANT and MONOTONE in the leak rate r** (the headline):
   the soft-analog-over-hard-3 advantage at rate r exceeds its leak-0 value. Derived shape (the
   falsifiable content beyond "positive"): the recovered fraction scales with the leaked-`|2⟩`
   population (∝ r at small r), modulated by the off-axis `|2⟩`-vs-`|1⟩` separation. NOTE `ΔF_soft`
   alone is a DIFFERENCE of two rate-growing floors (A3), so the *gate* is `Δ%ΔLER_leak`'s
   significance + monotonicity vs the leak-0 null, not "ΔF_soft grew." *(A flat/zero excess ⇒ the soft
   gain is generic readout softness, NOT leakage — the cap survives soft; a real reportable finding.)*
2. **Magnitude band (CONTEXT, not the leakage gate):** the absolute soft-vs-hard gain sits in the
   single-digit-% regime — **but Ali et al.'s 6.8%/5.0% is a TOTAL generic-soft-readout number
   (explicitly "have not leveraged leakage information," verified), the leakage fraction unquantified
   in the source.** So Ali is the GENERIC-softness envelope = the leak-0 offset to clear, NOT the
   leakage precedent; the leakage EXCESS (pred. 1) is expected to be a (likely smaller) part of it.
   (Pattison's +25% is a THRESHOLD improvement, not a %ΔLER — dropped as a numerical ceiling, A7.)
3. The leakage excess **grows with r** and (at d5+, PROVISIONAL — no oracle, verdict inherits the
   PROVISIONAL tag per §7) **with distance** (Varbanov: d5 more leakage-sensitive).
4. `headroom_soft → 0` as `c₂ → c₁` (L-soft-3, the no-fake-headroom control); reported as a CURVE over
   BOTH §2.2 bracket axes (`P(2→2)` AND the off-axis decomposition at fixed `P(2→2)`), never a single
   endpoint.

---

## 7. Epistemic-status audit (METRICS.md)

- §1 no-IQ-data conclusion: **(a) exact** (raw-artifact-verified). `p_m=½erfc(SNR/√2)`, `F_soft ≤
  F_binary` (data-processing inequality), the hardening-consistency identity `d2=1−2β₁`: **(a) exact**.
- §2.2 the `|2⟩` bracket: a **declared bracket** (FAITHFULNESS II.6) — default = "representative,"
  NEVER "physical truth"; the conclusion's bracket-dependence is reported (the sensitivity sweep).
- §3.1 `p_m` sweep, §6 `τ`-style thresholds: **(c) heuristic gates** (sweep/go-no-go only, never a
  premise). §3.2 the literature `|2⟩` numbers: **literature-grounded** with per-number confidence.
- §6 predictions 1–4: **(b) prediction bands** (registered bets; misses are findings).
- The d3 results are DM-feasible + carrier-certified (R≤2 bit-exact, χ*=4 τ=1e-3 R≤50); any d5/d7
  soft reading is **PROVISIONAL** (no oracle, ADR 0010) — reportable/gating only, never a premise.

---

## 8. Build plan (M3 — ≥3 disjoint agents, GPU-serial, un-led review)

The carrier (forward + LPDO floor), the seam, the binary floor, and the Pauli foil exist (ADR 0010 /
⑦); D2–D4 EXTEND them. Disjoint ownership: (D2) soft emitter + seam soft variant + L-soft-1/4/6/8;
(D3) soft floor estimator + the exact `k̄`-enumeration anchor + the inner-IS bias control + the
independent `f^{(2)}` check + L-soft-2/7/9/10; (D4) the baseline-hierarchy arms (hard-2 / hard-3 /
soft-MWPM / decoder-matched soft-NN+hard-NN / the leak-0 null) + the leakage-excess harness + the
two-axis (`P(2→2)` × off-axis) / rate / `p_m` sweeps. Each builder ships the FAITHFULNESS deliverables
(ledger passing on broken-input controls + the independent ground-truth check + the
bounded-simplification list) BEFORE "done." GPU-heavy agents serialize (exit-9 lesson); reviews run
GPU-light in parallel. **commit-gate:** every `src/` addition (the soft emitter, the soft floor
backend seam) needs user confirmation before commit; docs/outputs follow the normal flow.
**Perf note (ADR 0010 / handoff):** the LPDO floor is ~0.5 s/path (launch-bound); the soft floor's
`k̄`-marginalization adds cost (and the inner-IS is the L-soft-9 risk) — `batched-B` / CUDA-C++ is the
flagged followup before soft production scale.
**Docs follow-up:** a full reading note for Ali et al. 2403.00706 (the soft-surface-code precedent;
its model + the 6.8%/5.0% = generic-softness numbers verified here) → `docs/papers/reading_notes/`.

---

## Operating-model note (this D1 block)

**Review status: COMPLETE (this is the post-review revision).** The D1 build passed a 3-lane un-led
review (L-grounding/faithfulness · L-method/numerics · L-red-team/epistemic, each given only the doc +
the stage question) → orchestrator meta-review. All three returned PASS-WITH-FIXES; the meta-review
(a) verified the load-bearing findings against primary sources (Ali "have not leveraged leakage…" → the
6.8% is generic softness; Krinner 2.2%; the inner-`k̄` Jensen down-bias re-derived), (b) cross-checked
the convergent findings, and (c) added the baseline-hierarchy gap (hard-2 < hard-3 < soft). This
revision applies the consolidated fixes: the leakage-EXCESS headline metric + the leak-0 null (A1/A3),
the hard-2/hard-3/decoder-matched baseline hierarchy (gap-hunt/A4), the anchor reframe + `P(2→2)`→
geometry sweep (A2/F1/F2), the soft-floor inner-`k̄` control (L-soft-9) + independent `f^{(2)}` check
(L-soft-10), the de-vacuumed L-soft-4, and the §7 polish. **Next: D2, pending user confirmation** (the
design's two genuinely-new builds — the inner-`k̄` floor control and the hard-3/decoder-matched
baselines — get validated at D2/D3-build with their own controls, the natural place).
