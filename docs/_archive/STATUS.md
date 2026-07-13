# Project status & milestone history

Moved out of CLAUDE.md 2026-06-15 to keep the always-loaded control file lean.

## B path

B path validated on the rep-code toy:

- Label-free calibration recovers a coherent teacher (`calib_kl ≈ 0`).
- The `do()` knob matches the teacher's true ΔLER.
- Negative controls fail as pre-registered (moment-matched ≈ 900×, shuffled ≈ 1400× worse).
- Probe richness breaks the alias.
- Tier-0 bands cover truth and shrink with richness.
- d3 → d5 holds.

## HARDEN (H0/H1/H2)

H0, H1 and **H2** landed (2026-06-09).

- H2 ran theory-first: three exact theorems pre-registered, then verified 6/6.
- The factorized-learner fork is rung-indexed (b) → (a).
- `B_misspec` is real and functional-indexed.
- **Probe richness does not close the third band — one declared edge DOF does** (ADR 0006
  verdict: edge slots required for φ-sensitive functionals; carrier feasibility study unblocked →
  ADR 0008).
- The decision-regret Go/No-Go gate banked the **Claim-A floor** and deferred plan2's band engine.

## R2-lite (M1–M4)

**R2-lite M1+M2+M3 landed** (ADR 0007 Track B, `qec_twin/hardware/` + `tests/test_hardware_*`):
first real-hardware contact on the local Google d=29 release.

### M1

- Bit-exact m2d parity.
- Detection fractions in the derived band.
- Three back-edge findings: device mirror-diagonal class ≈970× the SI1000 sim, long-range tails,
  early-layer transient.

### M2

- Window closure adjudicated: single located grid-adjacent pair ⇒ 19 clean windows at margin 2.

### M3 (2026-06-10)

- **The window twin beats the shipped SI1000 prior on held-out hardware syndrome NLL in both
  bases** (+56.2 X / +44.3 Z nats/shot/window at one-sided 99%; drift-isolated fallback
  corroborates).
- Findings (post-A1–A3 addendum, 2026-06-10):
  - pij independent-edges deficiency is STRUCTURAL (bunching DOF unrepresentable; the
    budget-rescale control was a no-op — the global P10 deficit does not bind window constructions).
  - Located per-window bunching R̂ ∈ [1.0, 17.7] split-stable (≥2 on 17/19 X / 16/19 Z;
    w20 = 1.000 both bases).
  - Inter-sample drift (M5 feed).
  - P7's f̂ miss was a coordinate artifact — predictions hold on the identified flip-rate r̂
    (84%/81% in band, edge absorption sign correct).
- M3 GPU execution: static-Kraus-input CUDA graphs under the ledgered execution amendment — 84
  fits/22 min on one context, bit-exact vs eager at three pin levels (`hardware/m3_parallel.py`;
  model compute never falls back to CPU).

### M4 — decoder-prior utility (LANDED 2026-06-13)

- The one held-out pass (samples 05–09, both bases, d′\*=5) under frozen pymatching on the frozen
  M3 composition.
- The gate REVERSED: both calibrated DEM priors (self-computed pij AND the M3 twin) decode the
  held-out ~**40% WORSE** than the shipped SI1000 prior (%ΔLER twin-vs-naive −40.3% X / −40.7% Z
  vs the registered +10% bet — a (b) miss = finding).
- The HEADLINE twin-vs-pij is IN BAND at ≈0 (−0.33%/−0.60%): **the M3 syndrome-NLL win and the
  bunching certificate do NOT transfer to MWPM decoding through the independent-edges DEM format**
  (covariation NULL both bases; S10 routing GATE_FAIL_CALIBRATION_DIRECTION +
  COVARIATION_NULL_STRUCTURAL; PROVISIONAL, no mechanism attribution).
- The one decode-side positive: A3c two-pass +1.1%/+0.7% on high-R̂ windows (sig @99%).
- This is the registered "honest decode-end cost accounting" (rearguard, not the paper headline)
  and the strongest LER-level back-edge to the ADR 0008 carrier study.
- Execution integrity: a held-out decode is a fixed function of the frozen DEMs + sample bytes —
  proven by the ruling-28 bit-identity certificate (7 units sha256-identical across two attempts, a
  system OOM, two restarts; same certificate validates the ruling-25/27 shot-slicing throughput
  fix).
- A4 dMLE = documented-drop (none of the three upstream engines runs unmodified at the window
  instance within the 32 GiB/70 GiB envelope; `outputs/m4_a4_dmle_attempt_dossier.md`); the dMLE
  comparison is redirected to a registered r≈101 mid-scale bracket post-M4.
- M4 amendment 3 = rulings 19–28 (`docs/metric_results.md`).
- The suite is green (1 opt-in slow test skipped; hardware tests skip without `QEC_TWIN_HW_DATA`).

## ADR 0008 carrier study

ADR 0008 carrier study: charter + C1/C2 theory panel DONE (2026-06-10) + SEAM-TEST K1 first read
ABSTAIN (2026-06-11).

- Verdict: the **C1 composed architecture** (DEM/HMM bulk + window-exact CPTP coherent corrections;
  dMLE-TN as bulk engine + mandatory baseline; perturbative cross-seam module trigger-gated) is
  conditionally admissible under K1–K5.
- The dMLE TN is inadmissible as carrier (no coherent slot; bunching pinned at R=1 — the sharp
  T-B theorem: only unital-diagonal iid fields are pinned, non-unital CPTP expresses R>1 free).

## Current front + next

Next (M4 now banks the LER-level motivation):

- ADR 0008 carrier (the independent-edges bottleneck is now measured at the decoder).
- ∥ M5 drift (sample-indexed; M3/M4 drift findings are the input).
- ∥ the seam second read.
- The dMLE r≈101 bracket (own registration).
- H3/H4 sequenced by the bunching axis.
