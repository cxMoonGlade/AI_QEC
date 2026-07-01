# Pilot RESULTS — coupled-Lindblad-pseudomode v1 (n=2, N=1), reviewer-cleared

**Date 2026-06-30/07-01.** Outcome of the pre-registration
`coupled_pseudomode_pilot_prereg.md` §7/§8. Script (gitignored, local-only, re-run to rely):
`outputs/coupled_pseudomode_pilot_v1_n2.py`. GPU: RTX 5090 (eigendecomposition + propagation both
on `cuda:0`, verified). Epistemic tags: **(a) exact**, **(b) prediction/measured**, **(c) gate**.

> **Framing (2026-07-01, user): the goal is a QUANTUM ERROR COUPLING SIMULATOR, not the digital twin.**
> A forward simulator of coupled (correlated + non-Markovian) QEC errors; claim = FAITHFULNESS
> (oracle-certified) + value-over-factorized (the BLP/RHP wedge, decode-relevant via %ΔLER coupled-vs-
> factorized). The twin's inverse/causal loop (recover / do() / SCM / counterfactual / UQ) is OUT of scope.
> "Teacher" below = the forward controlled generator, not a teacher-for-a-learner.

## What was built
The first prototype of the **quantum error coupling simulator** (correlated + non-Markovian noise engine),
at the smallest scale: a shared non-Markovian bath causing **collective pure dephasing** on 2 qubits,
represented as **N=1 shared Lindblad pseudomode** via the published coupled-Lindblad-pseudomode
construction `[2506.10308, PRL 136 090403 (2026), Eq. 2-3, SM §S2]`, evolved as an exact CPTP GKSL
channel and certified against an **independent closed-form oracle** (the independent-boson
decoherence function — a Rule-I theorem, derived with zero reference to the pseudomode Lindbladian).

Target BCF: underdamped Lorentzian `C(t)=A e^{-iζt-γt}`, `A=g²` `[2602.21430 Eq. 20, n_β=0]`
(ζ=1, γ=0.15 underdamped / γ=4.0 overdamped control, g=0.5 — all **(c)** representative, physical
BCF grounding is a v2 item). Direct single-mode read-off `H=ζ, Γ=γ, g=√A`; `C^c(t)=g†e^{-iKt}g`
reproduces the target to **0.0e+00** (machine precision).

## Results (all measured 2026-06-30/07-01)
- **(a) BCF reproduction** `C^c==C`: **0.0e+00**.
- **(a) GKSL guardrails**: `max|Tr-1|=6.1e-14`, `max|ρ-ρ†|=4.6e-14`, `min_eig=-2.4e-15` (CPTP).
- **Cross-checks**: hand-built `L` vs `qutip.liouvillian` = **0.0e+00** (construction); GPU-eig ρ_S(t)
  vs `qutip.mesolve` = **6.3e-11** (integration). These certify construction+integration only; the
  physics certification is the independent oracle.
- **BET 3 — oracle agreement ≤1e-3: PASS.** `|00⟩⟨11|` (Δs=2 wedge) vs closed form = **2.5e-8**;
  `|01⟩⟨10|` (Δs=0 DFS) = **0.0e+00**. Single-qubit reduced coherence: the naive `½e^{-Γ_R}` fails
  (0.34) but the **Lamb-corrected** `½e^{-Γ_R}|cos Γ_I|`, `Γ_I=∫₀ᵗ(t-τ)Im C dτ`, matches to
  **2.0e-7** — a non-trivial, first-principles-verified sub-check.
- **Negative control — PASS.** A perturbed `g` (×1.5) drives the oracle disagreement to **7.3e-2**
  (≫ 1e-3): the certification is falsifiable, not vacuous.
- **BET 2 — wedge survives N=1: PASS.** Underdamped `|00⟩⟨11|` has a genuine coherence revival
  (pseudomode and oracle both 1 revival, matching amplitude); Γ' has 4 sign changes (revival-bearing
  BCF); overdamped control is monotone (0 revivals); `|01⟩⟨10|` DFS deviation from init = **0.0e+00**.
- **BET 4 — n_max cost (benign regime).** Peak mode occupation ⟨n⟩<0.4; n_max cost curve (@1e-3 → 6,
  @1e-4 → 8, @1e-6 → 10). A mid-circuit X gate raises ⟨n⟩ only 0.327→0.364 and does not move the
  n_max curve (the truncation error is set by the pre-gate ring-up; free/post-gate columns coincide).
- **BET 1 — polylog-N (SDP): DEFERRED** (single Lorentzian ⇒ N=1 trivially feasible; the multi-mode
  SDP / Loewner fit needs `cvxpy`, currently not installed).

**OVERALL v1: PASS** (bets 2+3 + exact fit), reviewer-cleared.

## Independent review (separate lane, un-led, read-only)
A separate-lane reviewer re-derived the construction and oracle from first principles against the
extracted paper text and confirmed: the enlarged Lindbladian, collapse operator, coupling `S`, and
BCF read-off faithfully implement `[2506.10308]` Eq. 2-3 / SM §S2; the oracle is genuinely
independent (Rule I) with **correct coefficients** (factor 1 on Γ_R, (Δs)²=4/0/1, the Lamb phase);
the column-stacking superoperator, partial traces, gate branch, and initial-coherence magnitudes are
correct; the negative control makes the certification falsifiable; **no blocking bugs**.

## SCOPE OF THE CLAIM (reviewer MAJOR-1 — read narrowly)
A PASS here certifies **the single-shared-mode (N=1) CPTP pseudomode embedding of collective pure
dephasing + the independent-oracle methodology**, at n=2. It is **not** a validated "correlated
cross-qubit non-Markovian shared-bath teacher." With one shared mode and a purely collective
`S=½(σz₀+σz₁)` the two qubits are **fully (rank-1) correlated**; the `|01⟩⟨10|` DFS protection is a
**Δs=0 tautology** of a collective operator, not evidence about structured correlated noise. The
load-bearing new pieces are **all deferred** to the n=3-4 increment:
- the **matrix-valued BCF** `C^c∈C^{n×n}` with **off-diagonal** cross-qubit terms (Δs≠0 partial
  correlation);
- the **SDP / Loewner fit** (`[2506.10308]` Eq. 8) that the polylog-N narrative rests on (needs cvxpy);
- the **ACE** second, method-distinct oracle (`[2405.19319]`; not installed here — the closed form
  fully certifies the exactly-solvable pure-dephasing regime, but ACE becomes load-bearing once we
  leave it, i.e. non-commuting gates / amplitude damping);
- bet 4's RWA-breaking cost, which is benign for pure dephasing (⟨n⟩<1) and is sharp only for the
  **amplitude-damping (JC)** coupling — where the closed-form oracle also no longer applies.

## Post-review reconciliation (2026-07-01) — primary-text 精读 + self-review + 3 architecture reviews

**Theory-first correction owned:** v1 was written from the reading NOTES, not the primary paper texts
(a theory-first violation — the handoff flagged the notes as `[PRIOR — re-verify]`). On the user's
prompt I 精读'd the PRIMARY text of `2506.10308` (main Letter + all SM) and the bet-4 section of
`2509.19685`, and verified the implementation against the actual equations. **Result: the construction
is FAITHFUL to Eq. 2 / SM §S2 — no bug was inherited from the note** — but the primary read + my own
adversarial pass + the three architecture reviews sharpen the scope and surface implementation issues.

**Sharpenings absorbed into the scope box (`outputs/coupled_pseudomode_pilot_v1_n2.py`):**
1. **N=1 single Lorentzian = the OLD "Lorentzian pseudomode" (Table I, refs [5,31,32]), NOT this
   paper's contribution.** At N=1 the coupled construction reduces to the decoupled Lorentzian mode
   (poly(T/ε)); the paper's dense-coupled H,Γ + SDP (Eq. 8) + polylog(T/ε) headline is UNTESTED.
2. **Paper demos Ŝ=σx (transverse); we use Ŝ=σz (pure dephasing)** — the exactly-solvable case (that
   is why the closed-form oracle exists), which sidesteps the non-commuting dynamics the method is for.
3. **"Exact CPTP GKSL" is exact only un-truncated;** what runs is the Fock-truncated (c) version
   (measured in bet 4). bet 3's 2.5e-8 is GUARANTEED by Theorem 1 (`C^c=C ⇒ ρ_S=ρ_S`), so bet 3 is a
   CODE-CORRECTNESS test, not a physics validation.
4. **Oracle independence is METHOD-level within the GAUSSIAN regime** (shared Gaussian-bath assumption
   with the pseudomode — `synthesis_review` Rule-I finding); it cannot certify a non-Gaussian source.
5. **RWA-breaking n_max (deferred JC arm) is a CPTP-faithfulness (positivity) question, not just cost.**
6. **The pilot required a NEW dense engine** — the existing per-site MCWF has no shared-bath
   representation (`synthesis_review` claim #15, CONTRADICTED "runs on existing engine").

**Implementation bugs found by running code (missed by the read-only reviews):**
- **`_count_revivals` amplitude was buggy** (returned ~tol, not true trough→peak) → made bet 2 look
  "marginal (2.07e-3)". FIXED; the TRUE wedge amplitude at γ=0.15 is **0.024** (|ρ| rises ×1.72) — a
  moderate, genuine revival. `outputs/coupled_pseudomode_pilot_v1_revival_robustness.py` characterizes
  the wedge vs underdamping (ΔΓ 0.36→0.14→0; unambiguous |ρ|×4, 6 revivals at γ=0.05; GPU pseudomode
  matches the oracle to 1.7e-7). **v1's γ=0.15 is a MODEST demonstration; γ≈0.08 should be the headline.**
- **Oracle factor-check (`fac<2e-3`) is grid-length dependent** — false-trips at γ=4 on a T=40 grid
  (2.04e-3). Should scale the 2-D integral resolution with T (main pilot uses T=25 where it is fine).

**Reconciliation with the three architecture reviews:** all agree the pilot is a *methodology smoke
test*, not a validated correlated teacher, and that the load-bearing pieces are deferred.
`architecture_review_post_jingdu` is optimistic (labels much "theorem-grade," d5/d7 feasible);
`coupled_teacher_architecture_critical_review` and `coupled_teacher_architecture_synthesis_review` are
appropriately skeptical (staged falsification; Gaussian shared blind spot; polylog = "theoretical
evidence"; "coherence-sensitive ΔLER" is a self-contradictory metric needing the METRICS.md ladder).
My read aligns with the skeptical pair; the `synthesis_review` claim-by-claim audit is the strongest.

## Next increment (n=3-4), each re-gated
1. Install `cvxpy`; implement the multi-Lorentzian / Loewner-SVD → SDP (Eq. 8) fit → `{H,Γ,g}` with a
   **dense** Γ; run the polylog-N bet (mode count vs T at fixed ε) on a QEC-relevant BCF.
2. **Matrix-valued** shared-bath: off-diagonal `C^c_{ij}` with **partial** cross-qubit correlation
   (Δs≠0), so the certification stops being a collective tautology; oracle = closed-form multi-qubit
   independent-boson (still exact for pure dephasing) + **ACE** as the method-distinct second oracle.
3. Amplitude-damping (JC) coupling arm for the genuine RWA-breaking n_max cost (ACE oracle needed).
4. Only on PASS of the above does any `src/qec_twin/**` land (commit-gate).
