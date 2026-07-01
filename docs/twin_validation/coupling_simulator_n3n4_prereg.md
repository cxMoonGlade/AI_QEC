# Pre-registration — quantum error COUPLING SIMULATOR, n=3–4 correlated-wedge rung

**Date 2026-07-01 (v3, post-review + self-review). Status: theory-first, PRE-BUILD, ONE theory gate open
(G2).** Written BEFORE any run; a miss is a FINDING, never re-fit. Supersedes the N=1 pilot
(`coupled_pseudomode_pilot_v1_results.md`). Anchored to the primary-text 精读 of `[2506.10308]` (Eq. 2-3,
SM §S1-S2), `[2509.19685]`, `[2602.21430]`, the BLP/RHP 精读 notes, and the ledgered metrics. Classes:
**(a) exact**, **(b) prediction band**, **(c) gate**, **PENDING-THEOREM** = class-(a) claim not yet derived.

## Revision log
- v1 → v2: two independent reviews (3-agent panel + codex) — folded 2×P0 / 5×P1 / 6×P2 / 2×P3.
- **v2 → v3 (author's own first-principles review, findings A/B/C the model reviews missed):**
  - **A (restructures the critical path).** The coupled-Lindblad **SDP + dense-Γ** is an **efficiency**
    (mode-count / polylog) optimization, **NOT the source of correlation**. The matrix BCF
    `C^c(t)=Σ_k(g_k g_k†)e^{-iλ_k t}` is a sum of rank-1 mode contributions; **cross-qubit correlation comes
    from SHARING modes across qubits (the matrix `g`), which works with DIAGONAL `H,Γ`.** And for a
    CONTROLLED simulator we **DESIGN** the shared-mode bath (no fitting), so the SDP/Loewner/cvxpy is not on
    the critical path. ⇒ the correlated-wedge rung uses a **naive multi-Lorentzian SHARED-mode bank** (diagonal
    `H,Γ`, matrix `g`, `N>1`); **no cvxpy, no SDP derivation (old G1), no dense-Γ (C8) on the critical path.**
    The SDP/coupled/polylog moves to a **deferred efficiency bet (§E)** — relevant only when fitting a
    *measured* device BCF with minimal modes at scale. (This also corrects v1/v2's own framing: leaving the
    N=1 tautology needs `N>1` *shared* modes — still the "naive" method — not the paper's coupled/SDP axis.)
  - **B.** The G2 oracle must be the **FULL COMPLEX** form (magnitude **+ Lamb phase**), not magnitude-only —
    the v1 pilot already proved the magnitude-only form fails (0.34) on sector-mixing coherences.
  - **C.** BLP/RHP on the full map measure **aggregate** non-Markovianity (the factorized diagonal has it too);
    the **contribution is the CORRELATED part** — the wedge metric must **isolate** it: `ΔN=N(coupled)−
    N(factorized)`, `ΔI` likewise, + the off-diagonal-specific coherence (partial-correlation breaks the DFS).

## §G. The one blocking theory gate
- **G2 — Multi-qubit closed-form oracle [PENDING-THEOREM → being derived in
  `g2_multiqubit_independent_boson_oracle_derivation.md`].** The primary Rule-I oracle. Derived from the BARE
  Hamiltonian `H_SB=Σ_i c_i Z_i B_i` via the Gaussian cumulant, **ZERO reference to the pseudomode `K,g,Γ`**.
  Full COMPLEX form (finding B): `ρ_{ab}(t)=ρ_{ab}(0)·exp(−Σ_{ij}(Δw)_i(Δw)_j Γ^R_{ij}(t))·exp(−iΣ_{ij}(w_i^a
  w_j^a−w_i^b w_j^b)Γ^I_{ij}(t))`, `w_i^a=c_i z_i^a`, `Γ^{R/I}_{ij}(t)=∫₀ᵗ(t−s)[Re/Im]C_{ij}(s)ds`, with
  `Γ^{R/I}` from the matrix BCF DIRECTLY. Reduction checks: n=1, n=2 rank-1 collective (v1), diagonal/private
  bath, sign/factor. Only after this may C3 be labeled `(a)`.

## 0. Framing (goal = SIMULATOR, not twin; correlation = shared modes, not SDP)
**Goal: a quantum error COUPLING SIMULATOR** — a forward simulator of coupled (correlated cross-qubit +
non-Markovian) QEC errors; claim = FAITHFULNESS (oracle-certified) + value over FACTORIZED simulators
(QMCtwin `[2606.19848]`, leakage-TN `[2308.08186]`). The twin's inverse/causal loop is OUT of scope.
**Correlation is carried by SHARED bath modes (matrix `g`), independent of the coupled/SDP efficiency axis
(finding A).** This rung DESIGNS a controlled shared-mode bath → a physical partial-correlation matrix BCF →
no fitting, no cvxpy.

## 1. Mechanism (ANCHORED — designed shared-mode bank; NO SDP on the critical path)
`[2506.10308]` SM §S2, the DIAGONAL-mode special case:
- **(a) `[VERIFIED-TEXT S2 Eq. S2–S4]`** `Ĥ_SA=Σ_{j=1}^n Ŝ_j Â_j`, `Â_j=Σ_{k=1}^N g_{kj}b_k+ḡ_{kj}b†_k`,
  matrix `g∈C^{N×n}`; matrix BCF `C^c(t)=g†e^{-iKt}g`. **Take `H,Γ DIAGONAL`** (decoupled underdamped
  Lorentzian modes, `H_{kk}=ω_k`, `Γ_{kk}=γ_k`) ⇒ jump ops trivially `√(2γ_k)b_k` (no C8 dense-Γ needed) ⇒
  `C^c_{ij}(t)=Σ_k g_{ki}*g_{kj}e^{-i(ω_k−iγ_k)t}`. `n=3–4` qubits, `Ŝ_j=Z_j` (`c=1`), Gaussian bath.
- **DESIGNED partial-correlation bath (controlled, (c)-representative):** choose `N=3–5` underdamped
  Lorentzian modes; make SOME shared across qubits (`g_{ki}` nonzero for ≥2 `i`) and SOME private
  (one-qubit) ⇒ off-diagonal `C^c_{ij}(t)≠0` with `0 < |C_{ij}| < √(C_{ii}C_{jj})` (PARTIAL, Δs≠0). Mode
  params grounded-representative (real 1/f/TLS grounding deferred). Underdamped (`ω_k>γ_k`) ⇒ the wedge.
- **REUSE the v1 engine's core Liouvillian construction**; the multi-mode (`N>1`) extension is new but small
  (diagonal Γ ⇒ direct); dense (exact, GPU) at n=3–4.

## 2. Observable — the LAYERED stack (ledgered), with the wedge ISOLATED (finding C)
- **Source/wedge layer — ISOLATED correlated non-Markovianity.** BLP `N(Φ)` + RHP `I` (ledgered). The
  reportable wedge is the **CORRELATION-attributable** part: `ΔN = N(coupled) − N(factorized)`, `ΔI =
  I(coupled) − I(factorized)` (a bare `N>0` is only non-Markovianity, which the diagonal already has). Plus
  the **off-diagonal-specific coherence** (partial-correlation breaks the `|ab⟩` DFS that the rank-1 case
  protected). Implementation split (matrix-BCF, not the scalar dephasing shortcuts):
  - **(c) quick witness** — selected-coherence trace-distance growth (fast falsification);
  - **(b) actual BLP** — `N=max_{ρ1,2}∫_{σ>0}σ dt`, declared random-pair search;
  - **(b) actual RHP** — `I=∫g(t)dt` from reconstructed intermediate maps (invertibility caveat). Do NOT
    assert "`I>0` ⇔ negative TCL rate" as the general matrix constraint (dephasing-class only).
- **Channel layer.** `D_Choi` = **full-channel** Choi trace distance `½‖J_coupled−J_factorized‖₁` at n=3–4
  (the ledger's per-seam form does NOT apply — full `2^n×2^n` Choi is direct); `1−F_e` (process infidelity) is
  a SUPPLEMENTARY, DISTINCT metric (Fuchs–van de Graaf-related, not identical); + Pauli-twirl distance +
  unitarity. **Predeclared FACTORIZED baseline** `J_factorized` = tensor product of per-qubit Gaussian
  pseudomode channels with the diagonal `C_{ii}(t)`, i.e. **all off-diagonal `C_{ij}` zeroed** (fixed
  construction, not an optimization).
- **Decoder layer (DEFERRED to code-scale) — named precisely.** `factorization_penalty =
  LER(factorized-DEM decoder on coupled records) − LER(coupled-DEM decoder on coupled records)` (a MODEL gap,
  **NOT** the ledgered decoder-prior `%ΔLER`); the ledgered PT-aware-vs-Markov `%ΔLER` on the same coupled
  process is a complementary metric. LER undefined on a 3–4-qubit non-code ⇒ deferred.

## 3. Independent ground truth (NON-CIRCULAR, Rule I)
- **PENDING-THEOREM (→ (a) once G2 closes)** the G2 full-complex multi-qubit independent-boson oracle. PRIMARY;
  a closed-form theorem via the Gaussian-cumulant path (different COMPUTATION from the Lindblad evolution —
  they share only the input BCF, which is the legitimate closed-form-vs-simulation check, not circular).
- **(b) ACE / PT-MPO `[2405.19319]`** — method-distinct 2nd oracle; **independence is METHOD-level WITHIN the
  GAUSSIAN regime** (declared).
- **(b) Non-Gaussian BOUNDARY characterization (NOT an acceptance gate):** ACE explicit-TLS (`add_single_mode`)
  — tests **single-site** non-Gaussianity ONLY; non-Gaussian *shared-bath* correlations need a future oracle.

## 4. Predicted behavior (FALSIFIABLE BETS — a miss is a FINDING)
- **(b) Correlated wedge is real + non-tautological.** For the designed partial-correlation (Δs≠0) bath,
  **ΔN>0 and ΔI>0** (correlation-attributable non-Markovianity), AND the `|01⟩⟨10|`-type coherence **decays**
  (partial-correlation breaks the rank-1 DFS). *Falsifier:* `ΔN≈ΔI≈0` with a fully-protected DFS ⇒ the design
  collapsed to rank-1 collective (report); or the only signal is a bare `N>0` = diagonal non-Markovianity
  (not the contribution).
- **(b) Oracle agreement.** Pseudomode `ρ_S(t)` matches the G2 FULL-COMPLEX oracle to **≤1e-3** (magnitude AND
  phase), and ACE to its tolerance, at n=3–4. *Falsifier:* >1e-3 not from a declared truncation → construction
  bug (STOP). *(Note: a magnitude-only oracle would falsely fail on sector-mixing coherences — v1 lesson.)*
- **(c) HARD GATE — wedge vanishes in motional narrowing.** ΔN, ΔI → 0 when the BCF is a NON-OSCILLATORY pure
  exponential (pure-dephasing TCL rate monotone, no sign change; matrix case: all `K=H−iΓ` eigenvalues Im<0).
  *(JC `γ_0/λ<1/2` belongs to the JC arm, not here.)* *Falsifier:* nonzero wedge in the non-oscillatory limit.
- **(c) GATE — n_max cost.** Gaussian dephasing displacement-governed (⟨n⟩<1); PASS if `n_max≤~10` @1e-6.
- **(b) Non-Gaussian boundary — a DISCOVERY, not a veto** (fail-strongly / match-widens-scope / unbounded-STOP);
  does NOT gate §7.

## 5. Bounded simplifications (declare + bound; UNBOUNDED = STOP, Rule III)
- **(a) Lorentzian-sum BCF fit residual** — bounded by `ε` within the fitted range. *(Moot on the core path:
  the bath is DESIGNED as a Lorentzian bank, so there is no fit — `C_ij` is exact by construction.)*
- **(c) 1/f tail via Lorentzian-sum** — HEURISTIC, UNBOUNDED (GLE bound voids for the branch cut, `[2402.11705]`);
  bracketed, never a premise. *(Only relevant to the deferred real-device-grounding step, not this rung.)*
- **(a→scope) Gaussian bath** — DECLARED; non-Gaussian handled only by the §3/§4 boundary characterization.
- **(c) Fock truncation `n_max`** — MEASURED.
- **(a) Dense eig vs MPS/TDVP** — n=3–4 dense is exact; the MPS χ-truncation for scale is a later gate.

## 6. Constraint ledger (Rule II — theorem + falsifier each)
| # | Constraint | Falsifier |
|---|---|---|
| C1 | CPTP: `H=H†`, `Γ⪰0` (diagonal Γ here) | `min eig(ρ(t)) < −1e-8` |
| C2 | Matrix BCF exact by design: `C^c(t)=g†e^{-iKt}g` = the designed `C_ij` | per-entry residual `> 1e-10` |
| C3 | Reduced dynamics = the G2 FULL-COMPLEX oracle (mag + phase) | coherence (mag or phase) vs oracle `> 1e-3` |
| C4 | Partial correlation genuine: `|01⟩⟨10|` DECAYS (not the rank-1 DFS) | DFS fully protected ⇒ secretly rank-1 |
| C5 | Correlated wedge isolated: `ΔN,ΔI > 0` from off-diagonal `C_ij` | `ΔN≈ΔI≈0` (only diagonal non-Markovianity) |
| C6 | Motional-narrowing control: `ΔN,ΔI→0` for a non-oscillatory BCF | nonzero in the non-oscillatory limit |
| C7 | **(discovery, not a gate)** non-Gaussian scope vs explicit-TLS | characterizes the boundary; does NOT block |

## 7. Acceptance gate (this rung)
**PASS** ⇔ (i) CPTP carrier with the designed matrix BCF exact (C1–C2); AND (ii) oracle agreement ≤1e-3 vs
the G2 full-complex oracle (+ ACE where run) (C3); AND (iii) the correlated wedge is real + non-tautological +
passes motional narrowing (C4–C6); AND (iv) `n_max` bounded. The non-Gaussian boundary is a (b) discovery,
NOT a conjunct. ⇒ proceed to (a) the **efficiency bet §E** (SDP/polylog, if pursued) and (b) the **code-scale
rung** (`factorization_penalty` + JC arm), which needs **MPS/TDVP** (the dense engine does NOT transfer;
χ-bound OPEN). **FAIL** ⇒ the failing constraint names the piece to re-scope; a null is an honest finding.

## §E. Deferred EFFICIENCY bet (OFF the core critical path — needs the cvxpy env fix)
The paper's coupled-Lindblad **SDP + dense-Γ** (Eq. 8, `[2506.10308]`): does it fit an EXTERNAL/measured matrix
BCF with **polylog(T/ε)** modes (vs the naive one-mode-per-pole diagonal bank)? **(b) bet:** `N≲8` @ε=1e-3.
Requires: (G1) the matrix/MIMO SDP construction derivation (shapes of `l,r,Y,K,g`; `Γ⪰0` proof), the dense-Γ
jump-op eigendecomposition (C8), and an **env fix** (cvxpy is INSTALLED but BROKEN — numpy 1.26.4 lacks
`numpy.lib.array_utils`; install a numpy-1.26-compatible cvxpy + SCS/Clarabel). This is the real-device-BCF
minimal-mode-fitting axis; it does not block the correlated-wedge-faithfulness claim.

## 8. Build plan (commit-gated, heavy-task + scripted-execution)
**Order:** close G2 (theory, docs — being done now) → `outputs/` prototype (NO cvxpy, NO `src/qec_twin/**`
until PASS + user OK): (1) build the DESIGNED shared-mode diagonal-Γ bank + matrix `g`; (2) enlarged CPTP GKSL
on n=3–4 ⊗ N modes (reuse v1 core Liouvillian; multi-mode extension new); (3) BLP/RHP (three-tier, ISOLATED
ΔN/ΔI) + channel `D_Choi`/`1−F_e` vs the predeclared factorized baseline; (4) G2 oracle cert + ACE (install/
repro) + explicit-TLS boundary. **Heavy-task:** ≥3 disjoint-ownership builders + a separate-lane un-led
reviewer BEFORE any GPU run; GPU serial; fan-out READ-ONLY.

## 9. Epistemic-status + staging
- **(a):** C1–C2 (identities), the metric definitions (ledgered).
- **PENDING-THEOREM (blocking):** G2 (C3). Not relied on until derived.
- **(b):** correlated-wedge-real (ΔN/ΔI), oracle-agreement, non-Gaussian-boundary (discovery), §E polylog.
- **(c):** n_max gate, motional-narrowing gate, quick witness, acceptance thresholds.
- **Standing-constraint note.** FAITHFULNESS_PROTOCOL "information–disturbance" and "Clifford ≠ dynamics
  invariant" are structurally INAPPLICABLE (forward simulator, not instrument/gate set); re-enter at the
  code-scale rung.
- **Staging:** THIS rung = the correlated-wedge simulator ENGINE + faithfulness + the isolated wedge (no cvxpy).
  Efficiency (§E, SDP/polylog) + decoder value (`factorization_penalty`) + JC/RWA arm = later rungs.

## 10. Immediate next step
Close **G2** (`g2_multiqubit_independent_boson_oracle_derivation.md`, with the four reduction checks) — being
done now. THEN the §8 designed-shared-mode prototype (no cvxpy). Reviewer before the GPU run. Slow is fast.
