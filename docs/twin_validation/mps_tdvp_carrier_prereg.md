# Pre-registration — MPS/TDVP carrier for the coupled-pseudomode coupling simulator

**Date 2026-07-01. Status: theory-first, pre-build.** The reviewer-sanctioned next infrastructure step
(after the n=3 correlated-wedge rung closed). Scales the dense GKSL (L is (d²)×(d²), d=2ⁿ·∏n_max — it
explodes) to an **MPS** carrier so larger n / a real code patch become feasible. Grounded in the primary
text `[2506.10308 SM §S4]` (the paper's own carrier: TD-DMRG/TDVP in the **vectorized-ρ superoperator**
formalism, cutoff 1e-12, **renormalize tr ρ=1 each step**, site ordering by dissipation magnitude) + the
repo's quimb MCWF-on-MPS conventions (`forward/scalable/mps_forward.py`: snake ordering, `gate_inds` + SVD
truncation, a discarded-weight ledger, cuda). Classes: **(a) exact**, **(b) prediction band**, **(c) gate**.

## 0. Decisions carried in (user, 2026-07-01)
- **complex64 (fp32) GLOBALLY.** Precision study (`outputs/coupling_simulator_precision_fp32_vs_fp64.py`):
  fp32↔fp64 discrepancy (~2e-5) is ~20× BELOW the Fock-truncation error (~4e-4 at converged nmax=5); fp32
  gives the SAME oracle accuracy as fp64 (4.38e-4 vs 4.37e-4); does NOT grow with dim (3.3e-5→2.2e-5 as
  L 4096²→10000²); ~3× faster + ½ memory ⇒ fp32 is not the bottleneck.
- **renorm guard REQUIRED** (fp32 trace drift ~3e-5/step; the paper renormalizes tr ρ=1 each step anyway).
- **Method = MPO W^II time evolution** on the vectorized-ρ MPS (CORRECTED 2026-07-01 after theory-first
  re-read — see `docs/papers/reading_notes/mps_time_evolution_methods_paeckel_1901.05824.md`). **NOT
  superoperator-Trotter/TEBD** (v0's error): the shared bath couples to a COLLECTIVE operator ⇒ the
  vectorized Lindbladian is **long-range**, and TEBD is nearest-neighbour (long-range ⇒ swap gates, awkward).
  Paeckel `[1901.05824 §4]`: the **W^II MPO** (Zaletel 2015) directly handles long-range, generates smaller
  MPOs than TEBD, and its only "downside" (non-unitary) is **natural for a Lindbladian**. The paper
  `[2506.10308 SM §S4]` itself uses **TDVP** (equivalent, arbitrary-Ĥ) — W^II is the tractable long-range
  dissipative variant. Deterministic (no MCWF √N curse). **Implementation (don't reinvent):** TeNPy has
  `ExpMPOEvolution` (W^I/W^II) + `TDVPEngine` built-in — NOT installed here (cf. cvxpy) ⇒ either install
  TeNPy (numpy dep) or build the W^II MPO on quimb (MPO-apply + compress; quimb has no W^II/TDVP class).

## 0.5 REVIEW UPDATE (2026-07-01 — three-review verdict + integrator decision)
The W^II prototype (`outputs/mps_wii_carrier_prototype.py`) was built and reviewed (codex GPT + deepseek +
Opus-self). **Core doubled-site/MPO mapping = CORRECT** (verified independently to 1e-15 vs index-loop defs,
1e-12 vs QuTiP `liouvillian`, 5e-4 vs a from-scratch analytic damped-dephasing oracle — agreement is NOT
circular). **But the artifact FAILS this prereg's gate as originally written**, and two predictions were wrong:
- **C4 FALSIFIED — W^II is O(dt¹), NOT O(dt²).** Zaletel's O(dt²) assumes Hermitian block relations
  (`C~B†`, `D†=D`); a Lindbladian MPO VIOLATES them ⇒ W^II degrades to first-order for the non-normal
  generator (confirmed: err ratios ~2.0 over 4 dt). Fundamental, not a bug.
- **C2 REFRAMED — positivity is not a hard gate for ANY scalable vec-ρ integrator.** The coupled-Lindblad
  GENERATOR is exactly CPTP (`H=H†,Γ⪰0`; the whole point of `[2506.10308]`), so the negativity we measured
  (`mps_wii_positivity_check.py`: dense min-eig POSITIVE +9e-5; MPS-W^II min-eig −9.15e-3 at dt=0.05 →
  −5.4e-4 at dt=0.00625) is a pure **W^II non-CP integrator artifact, O(dt), →0 under refinement** — NOT
  Fock truncation. Neither W^II nor TDVP is manifestly CP; manifest CP needs MCWF (trajectories) or LPTN
  (`ρ=XX†`, Werner `[1412.5746]` — but nearest-neighbour-only, fights our long-range bath). ⇒ C2 becomes:
  trace + Hermiticity EXACT; positivity = bounded O(dt)/O(χ) artifact, **reported per-step, NOT gated**.

**INTEGRATOR DECISION (user, 2026-07-01): HEAD-TO-HEAD W^II vs 2-site TDVP.** Both are grounded long-range
vec-ρ integrators; the tradeoff — W^II (clean MPO-apply, NO projection error, O(dt¹)) vs 2-TDVP (`[2506.10308
SM §S4]`'s own method, O(dt²), but tangent-PROJECTION error on the long-range shared bath) — is
coupling-structure-dependent ⇒ decide EMPIRICALLY by cost-to-target (accuracy + negativity + wall-time) on
1q+1mode then n=2. Manifest-CP carrier (MCWF/LPTN) for shot-sampling stays DEFERRED.

**Gap-fix list (before n=2 scale-up, all confirmed by review):** (i) wire the independent analytic oracle
into the harness (C6 is engine-vs-engine without it); (ii) add an ASYMMETRIC coupling test (cosθ·Z+sinθ·X)
— the symmetric Z-only case cannot certify the Rmul/(·)ᵀ-vs-(·)† convention; (iii) bound the nmax cutoff
(nmax=3 has ~1% coherence error vs nmax=6 — the reference itself is off by more than the MPS-vs-dense error,
so C6 measured the wrong floor) — validate at nmax=5–6; (iv) honor complex64 or drop the claim (ops are
currently cast to complex128 for TeNPy — the fp32 regime is UNTESTED); (v) add the positivity report to C2;
(vi) C1 and C5 are VACUOUS on 1q+1mode (C1 = two reps of one product state; χ=4 is the EXACT bond for 2
sites, min(4,9) — no truncation exercised) ⇒ real χ-truncation is only exercised at n≥2.

## 1. Mechanism (ANCHORED — the coupled-pseudomode Lindbladian, vectorized)
Enlarged Lindbladian `[2506.10308 Eq.2]` on n qubits ⊗ N diagonal-Γ pseudomodes (the reviewed shared-mode
design, finding A — no SDP): `dρ/dt = −i[H_A+H_SA,ρ] + Σ_k γ_k(2 b_k ρ b_k† − {b_k†b_k,ρ})`,
`H_A=Σ_k ω_k b_k†b_k`, `H_SA=Σ_k (Σ_j g_{kj}Z_j)(b_k+b_k†)`. **Vectorize** ρ → `|ρ⟩⟩` as an MPS over sites
[qubit₁..qubitₙ, mode₁..mode_N], local dim = phys² (qubit 4, mode n_max²). Build the **Lindbladian
superoperator L̂ as a block-triangular MPO** (on-site `H_A`/dissipator superops in the D block; qubit_j–mode_k
`Z_j(b_k+b_k†)` coherent-coupling superops in the B/C blocks — the shared-mode long-range coupling is an
off-diagonal MPO block with SMALL bond, which W^II handles exactly). Construct the **W^II time-evolution MPO**
`exp(L̂ δ)` `[1901.05824 Eq. 68–70]` and **apply it to `|ρ⟩⟩` + compress** (SVD χ-truncation) each step;
renormalize `⟨⟨I|ρ⟩⟩=tr ρ=1` each step; reduced `ρ_S` via `⟨⟨I_modes|`.

## 2. Observable / certification (the dense GKSL is the reference GT)
- **Primary GT (Rule I, non-circular):** the DENSE GKSL result already certified (n=2
  `coupling_simulator_n2_partial_correlation.py`, ρ_S(t) vs the G2 oracle to 4.4e-4; n=3 reduced). The MPS
  carrier must reproduce ρ_S(t) to the **dense-GKSL agreement floor** (≤ a few×1e-3, the fp32+truncation
  regime). Also cross-check vs the G2 closed-form oracle directly.
- **Bond/truncation ledger:** track max bond χ(t) + total discarded SVD weight (reuse the mps_forward
  `MpsTruncationLedger` pattern) — the load-bearing feasibility quantity.

## 3. Predicted behavior (FALSIFIABLE BETS)
- **(a) faithfulness:** MPS ρ_S(t) matches dense GKSL to ≤ the fp32+χ floor at n=2 (and n=3 reduced).
  *Falsifier:* disagreement ≫ the dense floor not attributable to a declared χ-truncation → construction bug.
- **(b) FEASIBILITY (the whole point):** for the pseudomode-enlarged **dephasing** simulator the MPS bond
  **χ stays bounded and small** (χ ≲ 16–32) as n grows — dephasing + a shared mode entangle weakly, so the
  vec-ρ MPS is compressible. *Falsifier:* χ grows exponentially in n / discarded weight blows up ⇒ the MPS
  carrier does not help ⇒ report + re-scope. This bet decides whether MPS/TDVP is the right code-scale carrier.
- **(c) speed/memory gate:** MPS beats dense at n≳6 (dense L=(d²)² explodes; MPS ~ n·χ²·phys²).

## 4. Bounded simplifications (declare + bound; Rule III)
- **(c) χ-truncation:** MEASURED (bet §3); discarded weight tracked, renorm each step.
- **(c) W^II time-step δt:** O(δt¹) for the non-normal Lindbladian generator (Zaletel's O(δt²) `[1901.05824 §4]` assumes Hermitian block relations `C~B†, D†=D`; a Lindbladian MPO VIOLATES them — verified experimentally in the W^II prototype, `mps_wii_carrier_prototype.py`: error ratios ~2.0 over 4 dt). Halved-δt convergence check required; positivity is O(δt) integator artifact →0 under refinement, NOT gated.
- **(a→scope) complex64:** bounded by the precision study (~2e-5 ≪ truncation); renorm guards trace drift.
- **(a) diagonal-Γ modes:** decoupled modes ⇒ per-mode local dissipators (no dense-Γ machinery) — the
  reviewed shared-mode design (finding A).

## 5. Constraint ledger (Rule II — theorem + falsifier)
| # | Constraint | Falsifier |
|---|---|---|
| C1 | vec-ρ init = product MPS of ρ0 (bond 1); tr ρ0 = 1 | `⟨⟨I|ρ0⟩⟩ ≠ 1` |
| C2 | CPTP: tr ρ(t)=1 (renorm), ρ(t) Hermitian, min-eig ≥ −tol | trace/hermiticity/positivity beyond fp32 floor |
| C3 | MPS ρ_S(t) == dense GKSL ρ_S(t) (same design) to the fp32+χ floor | disagreement ≫ floor not from declared χ |
| C4 | W^II time-step convergence: halve δt ⇒ error ↓ O(δt¹) (non-normal Lindbladian; O(δt²) is for Hermitian Ĥ only) | no δt-convergence |
| C5 | bond χ bounded (feasibility) | χ exponential in n / discarded weight blows up |
| C6 | reduces to dense when χ = χ_exact (no truncation) | MPS(χ_exact) ≠ dense |

## 6. Build plan (commit-gated; outputs/ prototype first, NO src until PASS)
`outputs/` prototype: (a) vec-ρ MPS + the Lindbladian **block-triangular MPO** (torch, **complex64**);
(b) **W^II MPO** `exp(L̂δ)` `[1901.05824 Eq.68-70]` apply+compress + χ-truncation + renorm guard + bond
ledger (TeNPy `ExpMPOEvolution` if installed, else quimb W^II build); (c) run the reviewed n=2 shared-mode design,
certify ρ_S(t) vs the dense GKSL + G2 oracle (C3, C6); (d) dt + χ convergence (C4, C5); (e) scale n=4→6 to
measure χ growth (the feasibility bet §3b). Reuse `mps_forward.py` quimb conventions. Separate-lane reviewer
BEFORE any scale run; GPU serial. Only on PASS (C1–C6 + feasibility) does a
`src/qec_twin/forward/scalable/**` carrier land (commit-gate).

## 7. Immediate next step
Prototype §6(a)+(b)+(c) — the vec-ρ MPS Lindblad evolution for the n=2 pseudomode design, complex64 + renorm,
certified against the dense GKSL. Reviewer before scaling. Slow is fast.
