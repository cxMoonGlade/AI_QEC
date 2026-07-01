# Pre-registration — few-qubit coupled-Lindblad-pseudomode SHARED-BATH teacher (oracle-certified pilot)

**Date 2026-06-30. Status: theory-first pre-registration, pre-build.** Written BEFORE any pilot run; a miss
is a FINDING, not re-fit. Anchored to 15 full-text 精读 notes (`docs/papers/reading_notes/`) + the synthesis
`coupled_teacher_architecture_synthesis.md`. Epistemic classes: **(a) exact/theorem/zero-tol**, **(b)
registered prediction band (a miss is a finding)**, **(c) heuristic go/no-go gate**. Load-bearing carrier
claims below were **verified this session against the extracted paper text** (not the agent note), tagged
`[VERIFIED-TEXT]`.

## 0. Purpose + why a pilot first
The core method is published (not ours to invent). This pilot answers, at **2–4 qubits**, the open
feasibility questions BEFORE any 2D/scale commitment — and doubles as the standalone anti-circular
**oracle-certification** the field lacks (QMCtwin concedes none exists). No `src/qec_twin/**` until the pilot
passes (commit-gate).

## 1. Mechanism (ANCHORED — reuse published method, do NOT invent)
Represent a **shared non-Markovian bath** causing **correlated dephasing across `n=2–4` qubits** as `N`
**shared pseudomodes** via the coupled-Lindblad-pseudomode construction `[2506.10308, PRL 136 090403, 2026]`:
- **(a) `[VERIFIED-TEXT 2506.10308 SM §S2 Eq. S2–S4]`** `Ĥ_SA = Σⱼ₌₁ⁿ Ŝⱼ Âⱼ`, `Âⱼ = Σₖ₌₁ᴺ gₖⱼbₖ + ḡₖⱼb†ₖ`,
  coupling **matrix** `g∈C^{N×n}`; matrix-valued BCF `C^c(t)=g†e^{-iKt}g`, `K=H−iΓ`. The n system operators
  `Ŝⱼ = Zⱼ` (dephasing on distinct qubits) share the SAME N pseudomodes → off-diagonal `C^c_{ij}(t)` = the
  cross-qubit bath correlation. Dynamics `dρ/dt = −i[Ĥ_S+Ĥ_A+Ĥ_SA,ρ]+D_A(ρ)`.
- **(a) `[VERIFIED-TEXT 2506.10308 Eq. 2]`** `H=H†, Γ⪰0` ⇒ the enlarged (qubits⊗N pseudomodes) evolution is
  an **exact CPTP GKSL channel, no memory kernel** — runs on our MCWF / 2D carrier (pseudomodes = truncated-
  Fock bosonic sites).
- **Target coupled BCF** `C_{ij}(t)`: from a shared **1/f/TLS** source represented as a **finite Lorentzian
  sum** — the a-priori-EXACT regime `[2602.21430 (JCP 2026); 2509.19685]`. Grounded to real-device 1/f/TLS
  parameters (later; pilot uses a declared representative Lorentzian).
- **Construction:** the **Loewner/SDP realization** `[2506.10308 S1]` fits `C^c(t)` to the target (robust,
  CONVEX — avoids non-convex fitting) → `{H, Γ, g}`.

## 2. Observable (the RIGHT one — not the retired strawman)
- **Primary — coherence-sensitive:** off-diagonal coherence decay `|ρ_{ij}(t)|` + the **coherence-revival /
  CP-divisibility-breaking** signature (the unforgeable non-Markovian wedge). `[2606.30569: correlation lives
  in coherence; 2412.13739: HS/syndrome metrics are coherence-BLIND]`. NOT populations, NOT cross-cycle
  syndrome correlation (Kam-benign, `[2410.23779]`).
- **QEC arm (deferred to the scale build, not this pilot):** decode-relevant **PT-vs-Markov ΔLER**, scored
  coherence-sensitively, via the PT-aware ML decoder `[2412.13739]`.

## 3. Independent ground truth (NON-CIRCULAR, Rule I)
Both are method-DISTINCT from the pseudomode-Lindblad carrier → no shared blind spot:
- **ACE / process-tensor** `[2405.19319]` — collective coupling `Â=Σⱼ Oⱼ` in one PT-MPO (path-integral,
  C++), non-Markovian-native; exercises the collective bath directly (its runtime success IS its verification).
- **Closed-form `C(t)`/`J(ω)`** `[2602.21430 Eq. 33 GT; 2509.19685 Eq. 40–45]` — the analytic BCF the
  pseudomode must reproduce (a `(a)`-class algebraic check on `C^c(t)=g†e^{-iKt}g`).

## 4. Predicted behavior (FALSIFIABLE BETS — a miss is a finding)
- **(b) Mode count.** `N` scales `polylog(T/ε)` on our QEC-relevant BCF **IFF** the SDP feasibility condition
  `[2506.10308]` holds. Bet: `N ≲ 8` for `ε=1e-3` over ~10 rounds of evolution. *Falsifier:* `N` grows
  poly(T) or the SDP is infeasible for our BCF → the polylog claim does not transfer; report + bracket.
- **(b) Wedge survival.** The coherence-revival (non-monotone `|ρ_{ij}(t)|`) survives `N=3–4` truncation.
  *Falsifier:* revival flattens at small N → truncation kills the wedge; report the N needed.
- **(b) Oracle agreement.** Pseudomode `ρ_S(t)` matches ACE + closed-form to **≤1e-3** (coherence-weighted
  infidelity / TVD) at 2–4 qubits. *Falsifier:* disagreement > 1e-3 not attributable to a declared truncation
  → a real construction/physics bug (STOP).
- **(c) GATE — RWA-breaking `n_max`.** Measure the pseudomode **Fock-truncation dimension** needed once the
  QEC gates (X/Y/CZ) act (which break excitation preservation, `[2509.19685]` open risk). PASS if `n_max`
  stays ≤ a declared bound (e.g. ≤4) at the required accuracy; FAIL (blows up) → the QEC application is
  cost-blocked and must be re-scoped.

## 5. Bounded simplifications (declare + bound; UNBOUNDED = STOP, Rule III)
- **(b→a)** 1/f as a finite Lorentzian sum: bracket the power-law-tail error vs the true kernel
  `[2509.19685: general baths get only an unbounded approximate fit]`.
- **(c)** Pseudomode Fock truncation `n_max`: MEASURED (bet §4-gate), not assumed.
- **(a)** Bosonic/Gaussian bath: a strongly-coupled non-Gaussian single TLS (telegraph saturation) is out of
  scope `[2506.10308]` — bracket, never claim.

## 6. Acceptance gate (the pilot's go/no-go)
**PASS** ⇔ (i) oracle agreement ≤1e-3 at 2–4 qubits (ACE + closed-form), AND (ii) the coherence-revival wedge
is preserved at a feasible `N`, AND (iii) the RWA-breaking `n_max` stays bounded. ⇒ proceed to the QEC arm
(multi-round space-time records + decode-relevant ΔLER + 2D-iPEPO composition), each re-gated.
**FAIL** ⇒ the specific failing sub-question (polylog / wedge-truncation / oracle / `n_max`) names the piece
to re-scope; a sub-floor result is an honest finding (per H2 discipline), never re-fit.

## 7. Build plan (commit-gated, heavy-task discipline)
`outputs/` prototype first (no src): (a) the SDP/Loewner BCF-fit → `{H,Γ,g}`; (b) the enlarged CPTP GKSL
evolution on 2–4 qubits + N pseudomodes (dense, small — exact, GPU); (c) the ACE + closed-form oracle
cross-check; (d) the coherence + revival + `n_max` measurements. Reviewer (separate lane) before the run;
GPU serial. Only on PASS does any `src/qec_twin/**` land (with user confirmation).

## 8. Immediate next step
Prototype §7(a)+(b)+(c) as a committed `outputs/` script measuring the four §4 bets against the oracle at
n=2 qubits first, then n=3–4. Slow is fast.
