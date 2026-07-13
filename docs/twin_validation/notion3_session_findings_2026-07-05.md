# Session findings + literature basis — notion-2 / notion-3 arc (2026-07-05)

> **HISTORICAL / TAXONOMY SUPERSEDED, 2026-07-13.** Retain the run facts, but do not reuse the
> old `K == notion-3 quantum memory` interpretation or the universal syndrome-twirl conclusion.
> Current authority:
> [`notion123_taxonomy_literature_closure_2026-07-13.md`](notion123_taxonomy_literature_closure_2026-07-13.md).

Synthesis of the 2026-07-04/05 arc: the corrected observable, notion-2 (classical multi-time memory), notion-3
(quantum non-classicality), the faithful-carrier corrections, and the theory-first grounding that reframed it.
This is the index; per-item detail lives in the prereg `§8`/`§10` post-run sections + the memory files.

## 0. The one-paragraph state

**notion-2 (classical multi-time record memory) = PASS, broadly achievable.** **notion-3 (quantum
non-classicality / K = Kolmogorov violation) = characterized ONLY through a suppressing lens** — `|++>` state
(σx₁ ⇒ K sign-blind), X-only axis (misses the complementary stabilizer), **pure σz-dephasing bath which
crow_joynt proves is CLASSICALLY SIMULABLE** (so K is limited *by theorem*, not by weakness), and coarse
joint-parity K (twirls the common mode → DFS collapse at |r|=1). **The genuinely-quantum component is RELAXATION
(σ−, non-unital), which is NOT classically simulable and lands on the COMPLEMENTARY (Z) stabilizer** — so the
FAIR notion-3 test (pending build) is **a multi-component bath (dephasing + relaxation) × dual-axis (X+Z)**.
Whether notion-3 is intrinsically fragile or was lens-suppressed is the OPEN question; do NOT conclude "fragile."

## 1. What was solved (accomplishments)

| # | result | evidence | grounding |
|---|---|---|---|
| S1 | emit() ~60× (byte-identical) | commit b603a81 | — |
| S2 | corrected observable = absolute multi-time Markov-order / CMI, error-A-clean | `corrected_multitime_observable_prereg.md` | Kam 2410.23779, Milz 1907.05807 |
| S3 | **notion-2 PASS** — passive record carries classical 1/f multi-time memory distinguishable from a Markov null, realistic coupling, all controls fire | `corrected_multitime_observable_run.py` (exit 0, sha 2560478e), prereg §8 | Kam, Milz, Zheng, dMLE, noise-spectroscopy |
| S4 | **declared-arm `K` separation** — quantum-bath arm `K>0` vs registered incoherent classical arm `K≈0`; corner-confined; no model-free origin claim | `notion3_quantum_vs_classical_run.py` (sha 7bef2895), prereg §8 | Milz/Smirne scope correction + internal run |
| S5 | faithful ancilla-mediated carrier (v2, both-coupled) — K NON-MONOTONE, collapses ~178× at r=1 (DFS) | `notion3_ancilla_mediated_run.py` (sha 823342df), prereg §10 | wang/hatifi/layden/botzung DFS |
| S6 | OQuPy PT/TEMPO independently reproduces K to ~5% (independent-GT for K) | `notion3_oqupy_pipeline.py` | — |
| S7 | K-peak diagnostic: peak REAL + Fock-converged (K↑~1.38× at |r|≈0.3, ↓ at |r|=1) | `notion3_Kpeak_diagnostic_run.py` (sha a55982df), prereg §8 | Budini superclassical |
| S8 | complete DFS/coupling-geometry grounding (10 papers) + the crow_joynt reframe | 3 preregs + memory | see §3 ledger |

## 2. What was exposed (errors caught + the trip-wire that caught each — see the `theory-fix` skill)

| error | what was wrong | caught by |
|---|---|---|
| error C "first-order" | classical memory is 2nd-order (cov)/4th-order (CMI), NOT first-order; "far more visible" retracted | literature (Quiroz/Srivastava/Dong) + derivation + κ-scaling slope 3.72 |
| v1 ancilla TAUTOLOGY | bath on d0 only ⇒ d1 inert ⇒ X_{d0}X_{d1}≡X_{d0} ⇒ record ≡ proxy; "K survives" was an identity | un-led reviewer (blocker) + non-degeneracy assert |
| 178× overestimate | single-qubit σx proxy overestimated the faithful joint-parity K ~178× (correlated common-mode twirled out) | the faithful (v2) carrier vs the proxy |
| **differential-rescues-K** | K predicted enhanced at r=−1 — FALSIFIED: σx₁ symmetry ⇒ K(r)=K(−r), sign-blind; r<0 = mirror tautology | **certified σx₁-symmetry control** (`notion3_sign_symmetry_control.py`, sha f4610a33) — trip-wire #1 |
| rate-vs-K conflation | the `[ours]` `K∝(1∓|r|)²` govern the dephasing RATE, not K (σx₁-even) | trip-wire #2 |
| "notion-3 fragile" (intrinsic?) | measured through a 4-fold suppressing lens on a classically-simulable component | user push-back + crow_joynt theorem — trip-wire #5 |
| C_pf==M_mem | the "two independent memory axes" degenerate on the symmetric records (structural identity) | un-led reviewer |

## 3. Literature ledger (all 精读, this arc)

**The corrected observable (notion-2):** Kam 2410.23779 (2-point insufficient; multi-time; Class-0/1/2 siting) ·
Milz 1907.05807 (Kolmogorov consistency = classicality) · Zheng 2601.22286 (syndrome learnability) ·
dMLE 2602.19722 (differentiable syndrome NLL — used as computation not learner) · Quiroz 2412.16092 +
Srivastava 2510.13051 + Dong 2502.05408 (classical dephasing/memory is 2nd-order — retires error C).

**giarmatzi/white/montanalopez** (2308.00750 / 2106.11722 / 2511.16772): full process-tensor identification
uses an intervention/tester family. A fixed passive record is a classical outcome distribution, but that fact
does not identify the underlying process as classical or prove that every restricted quantum witness is impossible.

**DFS / coupling-geometry (notion-3 mechanism):** wang 1409.0172 (`J_eff=(1−|r|)²`, DFS at r=1, bright at r=−1) ·
hatifi 2508.07046 (dark/bright modes, quadratic near DFS node) · layden 1903.01046 (DFS only at |g₀|=|g₁|) ·
botzung 2506.19631 (metastable DFS {|01⟩,|10⟩}, differential breaks it) · szankowski 1507.03897 (χ₁₂∝r,
sign reversal at r<0 — RATE, governs the rate not K).

**K = non-classicality witness:** budini 2301.02500 + 2411.13471 (**K ≡ DNI-violation**; r=1 = SUPERCLASSICAL =
memory without invasiveness; unitary s-e coupling generically violates DNI) · sakuldee 2204.11698 (multi-time
classicality ≠ single-round commutativity ⇒ the r=1 residual K) · lonigro 2211.02014 (single-qubit dephasing
classicality; the 2-qubit case is our gap) · gherardini 2101.11662 (instrument-dependence; invasive measurement
reduces memory).

**THE REFRAME (which noise is genuinely quantum):** **crow_joynt 1309.6383 (PRA, a-exact theorem): pure
dephasing + depolarizing = CLASSICALLY SIMULABLE (constructive classical field); relaxation / amp-damp /
non-unital = NOT** ⇒ notion-3 K lives in the RELAXATION sector, needs dual-axis.

**Multi-component bath MODEL + oracle:** chain_mapping 2407.10140 (shared bath, σz + σ− BOTH admissible; TN
oracle ≤6 qubits) · t_tedopa 2606.30569 (cross-spectral matrix) · arsenijevic 1606.01145 (AD+PD Kraus/magnitudes).

**Positioning:** shen/QMCtwin 2606.19848 (Lidar, d=7/97q — syndrome blind-spots for correlated/coherent noise at
scale, but does NOT compute K / common-vs-differential / multi-round = our gap).

**Tooling:** OQuPy PT/TEMPO = for CONTINUUM/1-f baths (independent-GT'd K to ~5%); numpy/QuTiP exact-Fock = for
single/few modes (current target) — `reference-bath-simulation-pipelines`.

## 4. The scope guardrails (do NOT re-cross — see the memory)

- **SIMULATOR, not twin:** faithfulness of the record vs independent oracles + anti-toy discriminability; NO
  recovery / NLL-learner / do() / active-probe-ladder ([[feedback-simulator-is-goal-twin-is-next]]).
- **DEM/decoder/LER out of the validity chain** ([[feedback-simulator-not-decoder]]); K/CMI/p_ij are internal instruments.
- **error-A trip-wire:** never `X − matched-marginal-null` as a discriminator; measure the ABSOLUTE order statistic.
- **classical 1/f = scaffolding; quantum GKSL bath = FINAL target** ([[project-coupling-nonmarkovian-is-the-contribution]]).

## 5. Immediate next step (grounded, pending build)

`notion3_relaxation_dualaxis_prereg.md` — multi-component bath (σz dephasing + σ− relaxation) × dual-axis (X+Z),
with the crow_joynt classical-field construction as the independent-GT. **Prediction:** relaxation K is robust
(broad, not corner/sign-blind/DFS) ⇒ notion-3 was lens-suppressed; **falsifier:** relaxation K also fragile ⇒
notion-3 intrinsically fragile. Either is a real finding. Build not yet launched.
