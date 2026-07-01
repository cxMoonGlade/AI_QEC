# Full-text review (focused) — Kubo, Ho, Goto, "High-performance multiqubit system with double-transmon couplers" (arXiv:2402.05361)

## Provenance

- **Source:** arXiv:2402.05361 [https://arxiv.org/abs/2402.05361](https://arxiv.org/abs/2402.05361), fetched 2026-06-30
- **Reading method:** FULL-TEXT read (精读) via arXiv HTML — all sections, equations, figures, and appendices
- **Status:** complete full-text close-read (focused read: abstract + sec. I intro in detail; pp.3-19 DTC circuit Hamiltonians skimmed as not load-bearing for effective-ZZ-channel teacher)
- **Note:** Original note built 2026-06-25 via PDF→txt (PyMuPDF, 19 pp) — this fetch confirmed the earlier reading

> **Provenance (2026-06-25): FOCUSED read.** PDF → txt `outputs/papers/2402.05361.txt` (PyMuPDF, 19 pp).
> 精读 of the abstract + §I intro (the load-bearing residual-ZZ magnitude); pp.3–19 (DTC circuit
> Hamiltonians + gate-simulation details for the double-transmon coupler) skimmed — NOT relevant to our
> effective-ZZ-channel teacher (we model the effective two-qutrit channel, not the coupler circuit).
> Read for the crosstalk-taxonomy theory-first (form 1, static ZZ).

## Metadata [paper]
- Authors: Kentaro Kubo, Yinghao Ho, Hayato Goto (Toshiba Corp. R&D / RIKEN RQC).
- arXiv:2402.05361v2, 21 Aug 2024. Type: theory / numerical circuit simulation.
- **Correction to our crosstalk lit-discovery:** it labeled this "Ni et al. 2024" — WRONG author. And it is
  a **Toshiba DTC** paper, **NOT a Google device** measurement.

## What it actually is [paper]
A numerical study of a 3-qubit chain coupled by **double-transmon couplers (DTC)** vs the standard
**single-transmon coupler (STC)**. Headline: the DTC suppresses residual couplings (incl. residual ZZ) to
≈0 even for highly-detuned fixed-frequency qubits, and enables 30-ns CZ + 10-ns π/2 pulses at >99.99%
fidelity (decoherence-free simulation). The paper's POINT is that the DTC *removes* ZZ.

## The load-bearing fact for us [paper → ours]
§I (p.1, lines ~48–50): "it has been reported that there is the so-called **residual ZZ coupling of
−80 kHz to −60 kHz for about 360 MHz detuned qubits** [ref 20]" — i.e. the STC-class residual ZZ. This is a
**cited** value (ref [20], the actual STC measurement), not measured here. Also notes (p.1, ~lines 53–55)
that small-detuning tunable-qubit + STC architectures instead "suffer from frequency crowding and
**microwave crosstalk**" (relevant to form 2, but not quantified here for our device).

## Relevance to qec_twin (form-1 ZZ) [ours]
- Confirms an **STC-class** residual-ZZ magnitude **|J_ZZ| ≈ 60–80 kHz** (highly-detuned regime). Useful as
  a SUPPORTING magnitude, but the primary STC source is its **ref [20]** (to chase if a tighter anchor is
  needed), and it is **NOT Google-specific**.
- **Still open (the real form-1 grounding):** (a) Google's actual residual ZZ during the QEC cycle — Google
  uses tunable couplers parked near the ZZ-null, so the *effective* per-cycle ZZ is NOT simply 60–80 kHz ×
  full-cycle; need a Google-device source (check `docs/.datasets/` + a Google surface-code paper). (b) the
  **θ = J_ZZ · t_eff** derivation: with J_ZZ ≈ 70 kHz and a 30-ns gate window, θ ≈ 2π·70e3·30e-9 ≈ **0.013
  rad**; over a longer effective integration time (hundreds of ns) θ grows toward ~0.1 rad. So θ depends on
  *how long* the qubits are off the ZZ-null per cycle — the lit-discovery's single "θ≈0.04–0.07" elided this.
- **Check vs our model:** `ws2_crosstalk_teacher.py` SWEEPS `φ ∈ {1e-3, 0.05, 0.10, 0.15}` (default 0.10).
  This brackets the gate-time θ (~0.013, between the 1e-3 and 0.05 points) AND the few-hundred-ns θ (~0.05–0.15).
  So the "ZZ too small" worry is unfounded *provided* t_eff is gate-to-few-cycle-window scale. **Falsifier to
  settle in the prereg:** derive t_eff for the Google d3-XZZX cycle; if θ(t_eff) > 0.15 the top of our sweep
  must be raised. (epistemic class (b) — a derived band to verify, not yet (a)-exact.)

## Limitations [paper]
Decoherence-free numerical simulation; 3-qubit chain; the DTC results are an alternative-coupler proposal,
not the Google device. The −60..−80 kHz STC number is cited, not independently re-measured.

## How to use / open questions [ours]
Cite as the STC-class residual-ZZ magnitude (with the ref-[20] provenance + the NOT-Google caveat). Do NOT
cite as a Google measurement. The Google residual-ZZ anchor + the t_eff→θ derivation are the next 精读/derivation
steps for form 1. Trust: focused read (intro fact solid; DTC circuit body not load-bearing for us).
