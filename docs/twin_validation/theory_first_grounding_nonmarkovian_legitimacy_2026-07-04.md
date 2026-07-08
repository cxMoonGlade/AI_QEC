# Theory-first grounding — the SIMULATOR's non-Markovian legitimacy signal (2026-07-04)

**Status: theory-first deliverable (literature-grounded), 2026-07-04.** All 15 named papers already had
committed 精读 reading notes; this synthesizes the LOAD-BEARING core (read in full this session: milz
1907.05807, noise_adapted 2411.09637, ziyad 2512.08893, RHP 0911.4270, BLP 0908.0238, Kam 2410.23779,
Zheng 2601.22286, dMLE 2602.19722, White-Pollock 2106.11722, Watkins-Quiroz 2501.06619, Bhardwaj
2511.09491). Epistemic tags: **(a) exact/theorem**, **(b) band**, **(c) gate/design**. Every anchored claim
carries its arXiv id. This RESOLVES the user's Problem-1 correction ("don't abandon classical non-Markovian;
legitimacy = CP-div breaking; right observable = multi-time, not 2-point") — confirming its thrust but adding
a **critical refinement the framing needs.**

## 0. The one-line correction the reading forces

The user's Problem-1 conflated two *distinct* notions of "non-Markovian." The literature separates them, and
**our current source has one but NOT the other:**

| # | notion | operational def | **our OneOverFDriftSource** (8 weak RTNs, Gaussian) | passive-syndrome-visible? | forgeable by | anchor |
|---|---|---|---|---|---|---|
| **1** | **CP-divisibility breaking** | reduced-map rate `γ(t)<0` ⇔ coherence revival ⇔ info backflow | **NO — CP-DIVISIBLE (RHP=BLP=0)** | coherence-twirled ⇒ likely NO (open) | requires the breaking regime | RHP 0911.4270 Eq4; BLP 0908.0238 |
| **2** | **classical multi-time record memory** | record's Kolmogorov Markov-order `> 1` | **YES** (1/f memory) | **YES** (streaks; learnable) | higher-order classical Markov/HMM | Kam 2410.23779; Zheng 2601.22286; milz 1907.05807 |
| **3** | **non-classicality (discord)** | record irreproducible by ANY classical process (Kolmogorov *violation*) | **NO** (classical source ⇒ Kolmogorov-consistent) | — | genuinely quantum only | milz 1907.05807 |

**(a-exact) The load-bearing physics:** classical Gaussian dephasing gives `ρ_01(t)=ρ_01(0)e^{−χ(t)}`,
`χ(t)=∫₀ᵗ(t−τ)C(τ)dτ`, so the RHP/BLP dephasing rate is `γ(t)=½∫₀ᵗ C(τ)dτ`. Our source has
`C(τ)=Σ_k v_k² e^{−2γ_k τ} ≥ 0` ⇒ **`γ(t) ≥ 0` monotone ⇒ CP-DIVISIBLE, RHP=BLP=0** (RHP 0911.4270 Eq 4:
`g=0` for `γ≥0`; BLP 0908.0238: no trace-distance backflow). The coherence decays **non-exponentially**
(memory, non-Markovian in sense 2) but **monotonically** (CP-divisible, Markovian in sense 1). ⇒ **anchoring
legitimacy on RHP/BLP would score our source ZERO** — the wrong signal for a classical Gaussian 1/f bath.

## 1. Deliverable (a) — is classical 1/f non-Markovian real / unforgeable / QEC-consequential / syndrome-visible?

- **Real + classical-applicable (user CORRECT):** RHP/BLP are reduced-MAP properties, classical dephasing
  included; a classical dephasing process with `γ(t)<0` breaks CP-divisibility (RHP 0911.4270, BLP 0908.0238
  central-spin example `γ(t)=AN·tan(2At)`). Milz 1907.05807: classicality = Kolmogorov consistency, a
  reduced-map/record property (no quantum substrate needed) — **point D confirmed.**
- **⚠ BUT our current source does NOT break CP-divisibility** (§0, a-exact). To reach notion-1 we need the
  **coherence-revival regime** — a strong/slow *single, non-Gaussian* RTN (Anderson–Kubo revival; `v>γ_sw`),
  reachable via `RTNSource`, NOT the 8-weak-RTN Gaussian `OneOverFDriftSource`. Its non-Markovianity is
  **notion-2 (classical multi-time memory)** only.
- **QEC-consequential (user CORRECT):** noise_adapted 2411.09637 — CP-*indivisible* noise makes standard
  stabilizer worst-case fidelity **collapse below 0.5** (`F²_min≈0.375` for [[5,1,3]] on non-Markovian AD;
  P-divisibility `dλ_k/dt≤0` violated on revival). Kam 2410.23779 — **streaky (multi-time) correlations on
  Class-1/2 are CATASTROPHIC** (power-law LER `p_L∝d^{−3.13}`, no teraquop, 97× at d=15). ⚠ noise_adapted's
  demo is *quantum* AD (not classical dephasing); Kam's is *classical multi-time* (notion-2, phenomenological,
  not CP-div). So the QEC-consequence is grounded for notion-2-on-the-record (Kam) and for notion-1-in-the-map
  (noise_adapted), by *different* papers.
- **Syndrome-visible (user CORRECT, for notion-2):** ziyad 2512.08893 (syndrome-as-memory: non-exponential
  `⟨Z̄⟩`); Kam (multi-time timelike-string streaks); Zheng 2601.22286 (spatiotemporal Pauli noise **learnable
  from syndrome ~2×10⁴ shots**). **For notion-1 on the passive record: LIKELY TWIRLED OUT** — Watkins-Quiroz
  2501.06619: ensemble-averaged classical-noise state is **block-diagonal in the stabilizer representation, no
  inter-sector coherence** ⇒ the syndrome distribution is classical; White-Pollock 2106.11722: a
  passive/unitary-only (no causal-break) record can **INFER but not DIRECTLY measure** the memory. ⇒ coherence
  revival (notion-1) may not survive the passive syndrome record — an open, possibly-negative result.

## 2. Deliverable (b) — the RIGHT passive-record observable

- **RETIRED:** 2-point detector autocorrelation / 2-point TV. Kam 2410.23779 §IV.C **proves** pairwise
  detector autocorrelation `p̄_{t,t'}` does NOT distinguish benign from catastrophic — the multi-time streak
  is the signature. (Confirms every prior "2-point insufficient" flag.)
- **The multi-time record instruments:** timelike-string / streaky structure (Kam); spacetime Walsh–Hadamard
  Pauli-eigenvalue learnability (Zheng 2601.22286, Thm 5 circuit-level); Kolmogorov Markov-order test (milz
  1907.05807 Eq 9 — instantiated on the detector-event distribution). Process-tensor `Υ` (White-Pollock,
  necessary+sufficient, Eq 11) is the gold standard but is **ACTIVE** (needs designed control + causal breaks)
  — for the passive simulator record it can only be *inferred*, so it bounds what the passive instrument can
  claim, it is not the passive instrument itself.
- **The FAITHFUL primitive (the objective):** exact **differentiable syndrome NLL** (dMLE 2602.19722) —
  `L(θ)=−E_{s∼data}[log p_θ(s)]`, exact partition-function/TN, **avoids the negative-rate / complex-`p_ij`
  pitfall** of correlation analysis, scales to d=5/r=25. Pauli/DEM-parameterized ⇒ it is the **strong
  stochastic baseline** (the Pauli-twirl); the repo already forks it (`cxMoonGlade/DMLE-QEC`). Use its exact
  syndrome-NLL as the faithful record objective; its Pauli-only limit is the negative control the coupling
  simulator's memory must beat.
- **The SLOW / quasi-static tail = DRIFT, read CROSS-SHOT (resolves the R=12 blind spot — user point B):**
  Bhardwaj 2511.09491 — the slow (`<1 Hz` TLS 1/f) component is a **time-varying MARGINAL rate** `g(t)`,
  recovered by **sliding/relative time-WINDOW** syndrome estimators (a Dirichlet low-pass, `W_opt≈0.12N/m_c`),
  scored by the **static-DEM LER penalty** — a *cross-shot / cross-round* statistic, NOT a within-shot lag.
  ⇒ the red-team's "R=12 slow tail is quasi-static within the shot" is not a wall: that component is a **drift**
  captured across shots/rounds, a *distinct* sub-axis from the within-shot correlation (Kam).

## 3. Deliverable (c) — the precise novelty gap

Adjudicated across the notes — **no paper lands "microscopic classical 1/f bath non-Markovianity certified on
the PASSIVE stabilizer syndrome record":**
- milz 1907.05807 — Kolmogorov classicality is generic single-observable; **explicitly NOT instantiated on
  stabilizer/syndrome records** ("our work", per its own note). No QEC.
- Watkins-Quiroz 2501.06619 — classical non-Markovian + stabilizer symmetry, but the result is **STATE-level**
  (block-diagonal DM), **no record/decoder observable** (W1). The classical-NM → syndrome-record bridge is
  unbuilt.
- noise_adapted 2411.09637 — CP-indivisible → QEC failure, but **quantum AD**, and about *recovery*, not the
  passive record.
- ziyad 2512.08893 — **emergent** logical NM (from QEC structure / syndrome not returning to code space), not
  an **injected microscopic bath**.
- Kam 2410.23779 — classical multi-time record + LER, but **phenomenological** (pairwise/streaky masks), NOT a
  microscopic bath and NOT the CP-divisibility / classicality connection.
- Zheng 2601.22286 / dMLE 2602.19722 — Pauli *learnability / estimation* from syndrome, not the
  "does bath non-Markovianity survive + how is it certified" faithfulness question.
- White-Pollock 2106.11722 — process-tensor NM is **ACTIVE** characterization (twin domain), and states the
  passive record can only *infer* memory.

**⇒ The unowned seam (the simulator's contribution):** a microscopic classical 1/f (sum-of-RTNs) bath, run
through the faithful forward, with its **notion-2 multi-time memory certified on the PASSIVE stabilizer
syndrome record** by the right observable (multi-time / exact syndrome-NLL, sited Class-1/2 where it is
decode-consequential), *and* the honest boundary that **notion-1 (CP-divisibility breaking) requires a
strong-RTN regime and is likely coherence-twirled out of the passive record** — the latter being itself a
publishable finding (a passive-record no-go for coherence-revival, or its survival if it does).

## 4. The reframed legitimacy gate (grounded) — what the next build should be

- **Legitimacy signal = notion-2 (classical multi-time record memory)** — our source HAS it, it is
  syndrome-visible (Zheng/Kam) and decode-consequential (Kam), and the passive record CAN carry it. NOT
  RHP/BLP (which are 0 for our Gaussian source).
- **Observable = multi-time / exact differentiable syndrome NLL** (dMLE primitive), NEVER 2-point. Report the
  memory as the record's departure from a Markov-order-1 / matched-marginal-independent model **measured
  multi-time**, with the forgeability hierarchy honest: **Level-1** beat memoryless (weak); **Level-3** = the
  1/f *power-law / multi-timescale* tail that **no finite-order classical Markov reproduces** (h2 §2b `E(k)`
  residual) — the genuinely unforgeable classical statement.
- **Siting = Class-1/2** (Kam 2410.23779, doubly-grounded now): Class-0 (data ZZ/T2) is BENIGN; the
  decode-consequential + strongly-visible memory needs Class-1 (syndrome SPAM) / Class-2 (CZ) — the ancilla
  axis the carrier defers (h2 §7.B).
- **Slow tail = drift axis** (Bhardwaj), cross-shot window + static-DEM LER penalty — separate from the
  within-shot correlation.
- **CP-divisibility breaking (notion-1) = the harder, more-novel claim** — requires re-parameterizing to a
  strong/slow non-Gaussian RTN (`RTNSource`, `v>γ_sw`) AND resolving whether coherence revival survives the
  passive record (likely twirled per Watkins-Quiroz / White-Pollock). Park as the deeper result; notion-3
  (quantum non-classicality/discord) is the quantum-bath line.

## 5. Epistemic status + provisional flags

- **(a) exact:** §0 CP-divisibility of Gaussian 1/f (`γ=½∫C≥0`); RHP Eq4; BLP contraction; milz Kolmogorov
  consistency; Kam 2-point-insufficiency; dMLE exact NLL = partition function.
- **(b) band:** the notion-2 memory `N_detect` on Class-1/2 (to be sized with the RIGHT observable — the prior
  Step-1 number was Class-0 + 2-point-flavoured, superseded).
- **(c) gate/design:** siting Class-1/2; the forgeability Level-1/3 ladder; drift vs correlation split.
- **Provisional (NOT built-upon):** "notion-1 is twirled out of the passive record" is PROVISIONAL (grounded
  by Watkins-Quiroz block-diagonality + White-Pollock passive-inference, but not yet computed in our setting);
  the novelty-gap claim (c) is PROVISIONAL pending a deeper-read confirmation of the remaining notes.
  **UPDATE 2026-07-04 (observable-correction session): full-text-read giarmatzi 2308.00750, tn_decoders
  2412.13739, montanalopez 2511.16772, Harper-Flammia 2303.00780** (re-confirming Kam/Milz). Net effect:
  the novelty gap is UPGRADED toward confirmed — the full process tensor `Υ` is ACTIVE (giarmatzi's
  measure-and-prepare causal breaks; montanalopez's designed W-layer; tn_decoders' comb is decoder/ΔLER-scoped,
  out of the simulator validity chain), so the PASSIVE-record classical multi-time order test remains unowned;
  and Harper-Flammia grounds the REALISTIC source (Sycamore ~0.136 avg, leakage/crosstalk, ~2× LER) that
  error B requires. Remaining provisional only on keeling, dong, spam_robust, vonlüpke, kattemolle, facets,
  layden (note-summary level). The corrected-observable run spec is [[corrected_multitime_observable_prereg]]
  (`docs/twin_validation/corrected_multitime_observable_prereg.md`), which supersedes the G0-v2/G6/G0-quantum
  matched-marginal-difference verdicts.
