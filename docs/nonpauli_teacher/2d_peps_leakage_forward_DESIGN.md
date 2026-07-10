# 2D PEPS Leakage-Forward Engine — Design (full Google d×d, d3 → d5 → d7)

Status: DESIGN (design-first, pre-build). 2026-06-23. Mainline code commit-gated.

---
## ✅ FEASIBILITY OUTCOMES (2026-07-09) — the §2/§correction(4) central question ANSWERED at d3

Three committed exact-DM measurements (`outputs/nonpauli_teacher/pepo_*_d3.py` + runners + logs
+ result jsons; every script un-led-reviewed pre-run — the reviews caught 5 blockers including a
float32 `1-eps` rounding that had silently corrupted the first run's chi(1e-8) column):

1. **R-gate — D_rho(R) SATURATES (`pepo_feasibility_drho_vs_round_d3.py`, VERDICT
   SATURATE_FEASIBLE).** The exact d3 rho evolved through R=1..10 within-cycle rounds
   (real leakage cell WG_L1=5e-3/g_seep=0.09/b=0.9 + NON-selective sequential Lueders channel)
   keeps the operator-Schmidt bond across the straight column cut at **chi(1e-6)=16, FLAT over
   10 rounds** (= the codestate's own operator rank: 2 crossing stabilizers → (2²)²); purity
   decays monotonically 0.991→0.915 (mechanism live); corrected chi(1e-8)≈50-53 (16 codestate
   values + spectral gap + ~35 tail components ≤1e-7 weight). Multi-round + leakage does NOT
   grow the PEPO bond — D-P's single-round feasibility extends along R.
2. **Record-gate — the eps map (`pepo_record_error_vs_eps_d3.py`, VERDICT RECORD_FEASIBLE,
   bond budget chi~16 at eps*=1e-3).** Per-round operator-Schmidt truncation at the cut
   (Hermitize + trace-renorm, error compounding across rounds) vs the exact sequential-null
   detector marginals: eps∈{1e-3,1e-4,1e-6} all truncate at the SAME chi=16 (the spectral gap)
   with max dp=6.65e-6 = **dp/bar=0.017 (60× margin) at N=1e6, z=4**; eps=1e-8 (chi~52) passes
   at dp/bar=0.039. FINDING: cutting AT the spectral gap beats cutting deeper into the tail
   (the gap-cut projects onto a round-stable subspace; the mid-tail cut keeps round-rotating
   noise directions) — the engine should truncate at the gap, not at a fixed eps. Declared:
   single-cut per-round truncation = OPTIMISTIC proxy (lower bound on engine error); the PASS
   eps is a NECESSARY bond budget, the engine's own gate is the sufficient check (§7 rung 1).
3. **xi-gate — the truncation-algorithm selector (`pepo_xi_correlation_length_d3.py`,
   adjudicated ITRSU_VIABLE_NTU_MARGIN).** Connected-correlator fits on the evolved state
   (lattice-spacing units, dynamic signal floor, ≥3-distinct-distance guard): dynamical
   **xi(Zq)=0.48, xi(n2)=0.18** — far below the itrSU validity bound xi≲2 (tePEPO), with NTU's
   xi~20 (Dziarmaga 2107.06635) a 40× margin. The Xq arm's automated NO_FIT is adjudicated
   (a)-exact BENIGN: its constant 2-pairs/1-distance/cmax=1.0 signal is EXACTLY the two
   weight-2 X-type boundary stabilizers (s1=X0X2, s6=X6X8, <XX>=1 structural, all other pairs
   <1e-4) — codestate structure the bond-16 PEPO carries exactly, not a decaying correlation.
   X2a mixture-algebra identity ~2e-16; **X2b: chi(mix)=chi(lo)=chi(hi)=16 every round — the
   global classical latent is BOND-FREE** (even stronger than the registered subadditivity),
   confirming the classical shared latent is SAMPLED or carried at zero bond cost; the unsolved
   PEPO+non-Markovian seam applies only to the parked QUANTUM-bath line.

**Consequences for the build:** the density-matrix PEPO route is GREEN at d3 (bounded D_rho,
bond-16 record-faithful with 60× margin, ultra-short-range correlations). Engine defaults:
**NTU truncation from the start** (Dziarmaga verdict; itrSU would suffice at d3 but NTU is the
10×-margin choice), truncate at the SPECTRAL GAP, classical latent via per-sample conditioning.
**Registered engine-build gates (Kilda 2012.03095):** the eps_Lambda convergence diagnostic +
the D=3..6 non-monotonicity sweep on OUR model + independent-oracle certification (never
D-sweep alone). **Scope caveats unchanged:** d-scaling (chi_b ~ D_rho^d ≲ 2^d) is an
EXTRAPOLATION — the d5 tile is rung 2; chi_b itself is measurable only inside the engine.
---

---
## ⚠ SUPERSEDING CORRECTION (2026-06-24) — read before the body below

The body (§1–§8) frames the engine as a **pure-state PEPS + MCWF**. That is WRONG for the full
d×d, and the novelty framing is too broad. Driven by the user's own prior-art research (full
primary sources, 3-0 adversarially confirmed). The body is kept for its constraint-ledger /
independent-GT / bounded-simplification / validation-ladder scaffolding (all of which transfer),
but the ARCHITECTURE and the NOVELTY/FEASIBILITY claims are replaced by this block. A clean rewrite
is the first task of the build session.

**(1) Prior art — 2D-PEPS-forward surface code is NOT novel.** Darmawan-Poulin 1607.06460
(PRL 119, 040502, 2017): full-2D PEPS, **density-matrix**, surface-code forward, arbitrary local
non-Pauli noise (amp-damp + coherent rotation, no Pauli-twirl), Born-sampled syndrome, **153 qubits,
single-round**. Also Lee 2504.04769 (PRR 2025); Rudolph-Tindall 2507.11424 (GPU + boundary-MPS
sampling, Willow square patches); Kshetrimayum-Weimer-Orús (Nat Commun 2017, dissipative/mixed PEPS).
So "full-2D PEPS forward" is occupied; D-P's 153q result also **settles the gross feasibility**
(d7 ≈ a few hundred qubits is reachable).

**(2) The only surviving delta (= the whole scope, INFRASTRUCTURE for the noise-twin):**
{full-2D PEPS} ∩ {explicit qutrit |2⟩ LEAKAGE} ∩ {MULTI-ROUND Born-sampled syndrome} ∩
{dual-bond (D_ρ, χ_b) truncation, certified vs the d3 DM oracle}. D-P = single-round, no leakage;
Manabe-Suzuki-Darmawan 2308.08186 = multi-round + leakage but THIN 1D strip. The intersection is
unoccupied. Position honestly as infrastructure + a narrow real delta — not a 2D-PEPS methods paper.

**(3) ARCHITECTURE CORRECTION — DENSITY-MATRIX PEPO, not pure-state MCWF.** The 1D MCWF was
efficient because an MPS has a CANONICAL FORM (cheap marginals/sampling). **A 2D PEPS has no
canonical form** → pure-state syndrome sampling needs ⟨ψ|Π|ψ⟩ = a DOUBLED-layer norm contraction,
χ_b ~ **D^(2d)** → the 2^(2d) wall RETURNS in the contraction (pure-state MCWF is the thin-strip
choice). D-P's **density-matrix Tr(ρΠ) is SINGLE-layer, χ_b ~ D_ρ^d**, and decoherence keeps D_ρ
low → that is why 153q works. So §3 below → **density-matrix PEPO + boundary-MPS contraction**;
leakage = a CPTP qutrit channel on ρ (no trajectory sampling); the two bonds are **D_ρ (operator)
and χ_b (boundary)**.

**(4) The narrowed feasibility question (the delta's real research question).** NOT "can 2D be
done" (D-P: yes) but: **does the MULTI-ROUND, leakage-bearing, full-2D density-matrix keep
operator-entanglement (D_ρ, χ_b) bounded as rounds accumulate?** Decoherence lowers it; multi-round
correlations + measurement back-action raise it — untested (D-P single-round, M-S-D thin-strip).
This is exactly what the §4 d3-DM-cert + a **bond-vs-round/d** measurement must answer BEFORE any d7
claim. The §7 ladder's gate becomes: measure D_ρ(R, d), χ_b(R, d) on d3/d5 → bounded ⇒ build d7;
grows ⇒ finding ("multi-round full-d×d hits its own wall").
---

## 0. Goal

A qutrit (phys_dim 3, complex128, GPU) **leakage forward simulator for the FULL rotated
XZZX Google surface-code patch** (d3 → d5 → d7), producing the syndrome + leakage record
(the teacher's surface-code data), via a **2D PEPS state + boundary-MPS contraction** — the
representation that reaches d7, which the 1D MPS provably cannot.

## 1. Motivation — why 2D, evidenced (the p11 finding, 2026-06-23)

`outputs/teacher_prereg/p11_codestate_ordering.py` measured the full-square codestate bond
under three 1D-MPS orderings (snake / column-major / RCM-min-bandwidth), d3 and d5:

| ordering | d3 exp/d | d5 exp/d | trend |
|----------|----------|----------|-------|
| snake    | 2.00     | 2.00     | pinned at 2.0 |
| colmajor | 1.58     | 1.80     | **rising toward 2.0** |
| rcm      | 1.86     | 1.92     | rising toward 2.0 |

The bond exponent **rises toward 2.0 with d** for every ordering; ordering buys a constant
factor only (d5: 512 vs 1024 = 2×), never an exponent. RCM is near-optimal min-bandwidth and
still cannot reach 1.0 ⇒ **2^(2d) is the 1D-MPS lower bound** for this patch family. A 1D MPS
pays the **pathwidth (~2d)** — a 1D sweep cannot realize a clean straight cut at every bond.
So d7 = 2^14 = 16384 = ~630 GB = **dead as a 1D MPS, any ordering**.

The **true area law** (a straight bisection, boundary ~d) is **2^d**. A 2D PEPS + boundary-MPS
contraction pays only that boundary: **d7 → 2^7 = 128** boundary bond → feasible *in principle*.

## 2. THE CENTRAL FEASIBILITY QUESTION (prevent-toy rule I — the real question)

**Manabe-Suzuki-Darmawan (arXiv:2308.08186, NJP 2025) — essentially our method, published —
chose the THIN 3×d strip and AVOIDED the full d×d.** That is a load-bearing datum, not a
footnote. The full-d×d 2D-PEPS contraction bond scales as **χ_b ~ D^d** where D is the PEPS
*state* bond. The codestate is D≈2 (a stabilizer-state PEPS) → χ_b ~ 2^d (feasible). But the
**EC dynamics grow D**; if D saturates at, say, 4, then χ_b ~ 4^7 = 16384 at d7 = the SAME WALL
in the contraction. So:

> **The build does NOT get to assume the full-d×d 2D PEPS is feasible at d7. It must MEASURE
> D(d) and χ_b(d) on d3, d5 (and as far as feasible) and show the boundary bond stays ≲ 2^d
> — i.e. that the EC area-law holds in 2D — BEFORE any d7 feasibility claim. If D or χ_b grows
> faster than the straight-boundary area law, the honest conclusion is "full d×d hits its own
> wall → the thin 3×d strip (the paper's choice) is the only feasible path," and that is a
> finding, not a failure.**

This question is the spine of the validation ladder (§7). Nobody claims d7 until it is answered
with measured bond-vs-d evidence.

## 3. Architecture

Pure-state **PEPS trajectory** (MCWF), mirroring the validated 1D MCWF-MPS engine one
dimension up. The state stays a pure 2D PEPS; the Born probabilities for sampling come from a
**boundary-MPS contraction**. Three modules (disjoint ownership, §6):

1. **Codestate PEPS** — build |m>_L for the rotated XZZX d×d patch DIRECTLY as a 2D PEPS
   (no dense 3^n, no 1D snake), qutrit-embedded, |2>-mass 0. A surface-code codestate is a
   stabilizer state → exact PEPS at bond D≈2 (XZZX mixed stabilizers: D≤4). Construction by
   the same projector formula as the 1D build ( ∏_g (I+g)/2 · (I+(-1)^m Z_L)/2 · |+…+> ), each
   ≤4-site stabilizer projector applied as a LOCAL 2D-PEPS gate.

2. **Local dynamics** — on the PEPS: leakage (qutrit WG model, MCWF jump, 1-site), syndrome-
   extraction gates (CZ etc., nearest-neighbour 2-site on the lattice), measurement projection.
   **Reuse the 1D engine's leakage channels + within-cycle schedule verbatim** (the physics is
   identical; only the host TN changes). PEPS state bond D truncated with a discarded-weight
   ledger.

3. **Boundary-MPS sampling** — to sample a stabilizer outcome, compute its Born probability
   ⟨P⟩ by contracting the PEPS expectation via a boundary MPS of bond χ_b (sweep rows, compress
   with **gesvd**); sample the outcome; collapse (project) the PEPS; continue. χ_b truncated
   with a discarded-weight ledger.

**Two truncations, both load-bearing**: the PEPS state bond **D** and the boundary bond **χ_b**.
Both are bounded simplifications (§5) and both are validated against the d3 DM oracle (§4, §7).

## 4. Independent ground truth (prevent-toy rule I)

The d3 **DM-exact (s,f) joint oracle** (`outputs/teacher_prereg/p7e_carrier_cert_common.py`,
`DMPathEvaluator`), which is INDEPENDENT of any TN (dense density-matrix path-propagation). The
PEPS forward's (s,f) joint distribution **== the DM oracle at d3, within the MC band, zero
structural tolerance** — the same bar the 1D engine passed (p9d). This certifies the PEPS
engine end-to-end at d3 against a non-TN reference (NOT against the 1D MPS — that would be
circular: two TNs sharing a blind spot).

## 5. Bounded simplifications (prevent-toy rule III — declare + bound each)

- **PEPS bond-D truncation** — class (a) state book; bounded by per-cut Schmidt discarded
  weight; faithfulness = d3 observable invariance vs DM as D grows (p9f-analog).
- **Boundary χ_b truncation** — class (a); bounded by boundary-MPS discarded weight; faithful-
  ness = d3 observable invariance vs DM as χ_b grows.
- **WG qutrit leakage model** — already declared + bounded in the 1D engine (Wood-Gambetta
  C_L ≤ 2√(L(1−L)); reuse, do NOT re-derive).
- **Per-CZ-layer leakage injection (Stim structural timing, the T4 simplification)** — reuse
  the 1D engine's declaration; unchanged by the 2D host.

Unbounded simplification = STOP (rule III).

## 6. Agent decomposition (heavy-task rule: ≥3 disjoint-ownership builders + a reviewer)

- **A1 — Codestate-PEPS builder**: §3.1. Owns the d×d PEPS codestate; deliverable = exact d3
  PEPS == d3 dense codestate (independent), structural cert (⟨S⟩=+1, ⟨Z_L⟩, |2>-mass=0) at d5.
- **A2 — Dynamics builder**: §3.2. Owns the local PEPS ops (leakage/gates/measurement), reusing
  the 1D leakage channels + schedule. Deliverable = a single PEPS round runs + stays CPTP.
- **A3 — Boundary-MPS sampling builder**: §3.3. Owns the boundary contraction + Born sampling +
  collapse + the χ_b ledger + gesvd. Deliverable = stabilizer Born probs vs a small-d brute check.
- **A4 — Validation builder**: §4 + §7. Owns the d3 DM-cert + the D,χ_b faithfulness sweep +
  the bond-vs-d feasibility measurement (§2). Deliverable = the validation ladder scripts.
- **Reviewer (independent, un-led)**: reviews THIS design + the integrated engine. Briefed with
  the stage problem + ultimate goal + the artifact ONLY (no diagnosis/conclusions). Central
  charge = the §2 feasibility question: is the full-d×d 2D PEPS genuinely d7-feasible, or does
  it hit its own D^d wall (→ thin strip)? Find the holes.

Substrate: quimb 2D TN (`quimb.tensor.PEPS` + boundary contraction), as the 1D used quimb MPS.
GPU-only, complex128. Scripted-execution for every run (asserts + printed evidence + flushed +
`__main__` guard).

## 7. Validation ladder (no d7 claim until each rung passes)

1. **d3 — exact**: PEPS forward (s,f) joint == DM oracle (independent, zero structural tol);
   D,χ_b faithfulness (observable invariant as D,χ_b grow, vs DM).
2. **d5 — no DM oracle**: D,χ_b convergence + discarded-weight bound (the truncation MECHANISM
   is certified at d3; d5 carries the extrapolation caveat explicitly).
3. **d7 — feasibility FIRST**: measure D(d), χ_b(d) on d3/d5(/d7-codestate); show ≲ 2^d (the §2
   gate). ONLY THEN the frontier number (a real full-2D d7 forward run + its cost). If the bond
   grows faster than the straight-boundary area law → report "full d×d hits its own wall, thin
   strip is the feasible path" (a finding).

## 8. Reuse (nothing from the 1D effort is wasted)

qutrit WG leakage model · within-cycle schedule parsing (real Google patches) · the DM-exact
joint oracle (`p7e_carrier_cert_common`) · **gesvd** SVD driver · the **p9f** truncation-
faithfulness METHOD (now on D and χ_b) · the 1D mainline `mps_forward.py` stays valid for d3 +
the thin 3×d strip. The 1D full-square d5 work validated the engine + leakage + DM-cert
methodology — all carried up one dimension.
