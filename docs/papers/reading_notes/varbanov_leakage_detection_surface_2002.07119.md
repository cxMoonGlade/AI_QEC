# Full-text note (focused 精读) — Varbanov, Battistel, … DiCarlo, Terhal, "Leakage detection for a transmon-based surface code" (arXiv:2002.07119)

> **Provenance (2026-06-25): FOCUSED 精读.** PDF → txt `outputs/papers/2002.07119.txt` (PyMuPDF, 21 pp;
> one stray null byte — read via the Read tool, located via `grep -a`). Close-read of §I-A (the leakage CZ
> model + conditional phases), §II (the defect-probability fingerprint), and Appendices H+I (superleakage
> |3⟩ + leakage mobility, the |2⟩-vs-|3⟩ gap). HMM detection scheme (App E/F) + IQ readout (App C) skimmed.
> For the path-B crosstalk theory-first (the leakage-TRANSPORT edge_field channel). npj QI 6:102 (2020);
> QuTech Delft + Google. Density-matrix Surface-17 (d3), qutrit, in **quantumsim** [open-source].

## Why load-bearing [ours]
The most directly IMPLEMENTABLE leakage-CZ channel in the literature: a **parametrized qutrit (|2>-only) CZ
leakage model** (+ an App-H |3> extension), with an **explicit second-order-gap result** that quantifies our
two-arm (|2>-only vs |3>-faithful) decision. Complements Miao 2211.04728 (the Google hardware rates) with a
concrete simulator channel form + the approximation gap.

## The CZ leakage channel (the |2>-only / qutrit recipe) [paper → ours]  §I-A
Per CZ (Q_flux = higher-freq qubit; Q_stat = partner). Three pieces, applied as instantaneous maps in quantumsim:
1. **Computational phases:** φ00=φ01=φ10=0, φCZ=φ11=π; φ02=−φ11=−π (flux-based, qutrit rotating frame).
2. **Leakage exchange |11>↔|02> (the leakage SOURCE, rate L1):**
   `|11> ↦ √(1−4 L1)|11> + e^{iφ}√(4 L1)|02>`, `|02> ↦ −e^{−iφ}√(4 L1)|11> + √(1−4 L1)|02>`.
   (The phase φ + the |11><02| off-diagonals are set to 0 for efficiency — App B; "do not affect the
   results.") Default **L1 = 0.125%** per CZ.
3. **Leakage CONDITIONAL PHASES (the spatial-crosstalk PHASE — the dominant spatial effect at low L1):**
   - Q_flux leaked, Q_stat not → on {|02>,|12>} the gate is `diag(e^{iφ02}, e^{iφ12})` = (up to global phase)
     a **Z-rotation on Q_stat by `φ_L^stat := φ02 − φ12`**.
   - Q_stat leaked → Q_flux gets `φ_L^flux := φ20 − φ21`.
   - Non-trivial (φ_L^stat ≠ π, φ_L^flux ≠ 0) due to the 3-excitation manifold shifting |12>,|21> (App H). If
     |12>-|21> is the only interaction: φ12=−φ21 ⇒ `φ_L^stat = π − φ_L^flux`.
   - **SWEEP DISCIPLINE, canonically grounded:** "φ_L^flux and φ_L^stat are **RANDOMIZED** for each qubit pair
     across runs (not across CZ gates within a run)… as they have **not been characterized in experiment** and
     we instead capture an average behavior." → our phase is a SWEPT/RANDOMIZED band, NOT a frozen 0.65π
     (Miao's 0.65π is one device realization; this is the model-level treatment to copy).
4. The **|11>↔|20> crossing is clean** (2α off-resonant → <0.1% phase/population) — the CZ ITSELF is
   qutrit-faithful (matches Barends 1907.02510). |01>↔|10> (J1) suppressed <0.5%.

## The |3> extension + the |2>-vs-|3> GAP (Appendices H, I) [paper → ours] — the decisive result
- **Superleakage L3 := |<03|S_CZ(|12><12|)|03>|² (Eq H2):** the |12>↔|03> avoided crossing at ω_int+|α|
  (coupling √3 J1) transfers |12>→|03> (a near-diabatic Landau–Zener passage). "L3 can be **high** depending
  on the flux-pulse parameters." Each superleakage event is **accompanied by a bit flip on a neighbour**
  (coherent |03>↔|12> exchange) → raises defect probabilities + LER.
- **Leakage mobility L_m := |<21|S_CZ(|12><12|)|21>|² (Eq H3):** the |12>↔|21> SWAP transport. WITHOUT |3>:
  "small but non-negligible" (off-resonant |12>-|21>, coupling 2J1). **WITH |3>: L_m grows** via a two-
  excitation **|03>↔|21> resonance virtually mediated by |12>** (|03> and |21> ON resonance at the interaction
  point; effective coupling ≈ (2J1)(√3 J1)/α ≈ **2.6 MHz**, Eq H4). ⇒ **|3> ENHANCES the transport** (this is
  the |3>-necessity mechanism the deep-research flagged — CONFIRMED from source).
- **App I — the GAP, quantified:** sweep `L_m ∈ [0, 1.5%]` at L1=0.125%, randomized phases.
  "**Leakage mobility has a NEGLIGIBLE effect on the logical performance… because it is only significant for an
  ALREADY-leaked qubit, which occurs with low probability given the low L1 per CZ. The leakage swapping
  between neighbouring qubits is a SECOND-ORDER effect**" (verbatim sense). They did NOT run Surface-17 with
  |3> on any qubit (prohibitive cost). ⇒ **the transport contribution scales ~ O(L1 × transport_fraction) =
  second-order in the leakage population.**

**[ours] The two-arm gap prediction (falsifiable, for the d3 DM-oracle gap test):**
`Gap(|3>-faithful − |2>-only) ≈ 0 at low leakage (L1 ~ 1e-3, Varbanov App I says negligible), and GROWS with
the leakage population (toward Miao's un-removed-regime dominance).` So |2>-only is a DEFENSIBLE approximation
with a SECOND-ORDER-in-L1 bounded error in the DQLR-deployed/low-leakage regime — and the |3>-arm matters only
as leakage rises. This is the declare+bound, now grounded in a published gap sweep, not assumed.

## The detector fingerprint (the falsifiable validation target) [paper] §II, App D
- Leakage is **sharply projected** → a **LOCAL increase in the defect probability of NEIGHBOURING stabilizers**
  (the spatial signature; §II, Fig 2–3). Post-selecting leakage restores LER below break-even (discards ~47%).
- **Weight-3 anti-commuting checks → pd ≈ 0.5** when a qubit is leaked (App D). [ours: pd≈0.5 is NECESSARY but
  NOT transport-unique — cf. Kam 2410.23779 "2-point can't grade severity"; pair it with Miao's non-local
  p̄_{t,t'}>1% at |t−t'|>1.]

## Independent ground truth this supplies [paper → ours] App H (Eq H1)
The **full multi-level transmon-pair Hamiltonian** (Eq H1: ω, α, J1(Φ(t)) tunable coupling) + full-trajectory
simulation of the diabatic flux pulse — a from-scratch, channel-INDEPENDENT computation of φ_L, L1, L_m, L3
from the bare couplings + detunings. This (or our own re-derivation of it) is the NON-CIRCULAR GT for our
edge_field channel — NOT our engine's oracle. (g_eff/P_t in Miao SI S1 is the analytic version of the same.)

## Limitations / caveats [paper]
- L_m/L3 are **device/flux-pulse specific** (Net-Zero pulse, fast-adiabatic) → SWEEP, don't freeze.
- App I only put leakage mobility on high-data↔ancilla pairs (DM-size constraint); never ran |3> on any qubit
  in Surface-17 (cost) — so the |3>-faithful-at-d3 LER is NOT measured here (we'd be first to, on the DM oracle).
- The phases φ_L are randomized (averaged), not the true device values — a model choice, not a measurement.
- Low-L1 regime (0.125%); the "second-order negligible" conclusion is FOR low leakage — it does NOT bound the
  high-leakage (un-removed) regime, where Miao shows transport dominates.

## How to use / trust [ours]
- **Cite for:** the implementable qutrit CZ leakage channel (exchange + conditional phases, randomized); the
  L_m/L3 definitions (Eq H2/H3) + the |03>↔|21> |3>-enhancement (Eq H4); the **second-order gap** (App I,
  transport negligible at low L1); the neighbour-defect-probability + pd≈0.5 fingerprint; the multi-level
  Hamiltonian as independent GT.
- **Do NOT cite for:** a measured |3>-faithful d3 LER (they didn't run it); a high-leakage transport bound
  (their negligibility is low-L1 only); frozen phase/transport values (randomized/device-specific).
- Trust: focused full-text 精读 of the load-bearing §§ + App H/I; figures-not-pixel-extracted.
