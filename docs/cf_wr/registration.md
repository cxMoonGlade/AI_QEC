# CF-WR pre-registration draft v2 — 12q Teacher windowed-reconstruction feasibility verdict

> Status: **FROZEN 2026-06-14** (3 rounds of adversarial review passed: R1/R2 BLOCK→fixed, R3 MINOR→fixed; of-record stub in `docs/metric_results.md`).
> **Pre-run Amendment 1 (2026-06-14, build scout found G1):** D_Choi changed to **per-seam reduced-block Choi trace distance** — the full 2²⁴ channel Choi is infeasible, changed to per-seam reduced-channel Choi blocks on ≤6q support (≤2¹² dim, feasible); **the global 2²⁴ is never materialized**, global = seam aggregate (= P4 L-scaling); the GO gate uses the per-seam value at R̂≈5.3 against the per-seam √(I_nats) bound. **G2 (no 2D substrate): build directly** (3×4 geometry / 2D detector map / line-seam glue / 2D decoder all built from scratch, build the frozen `cf_wr_geom` contract first).
> owner's three decisions (2026-06-14): **(i) go directly to P2 (2D fragments)**; **(ii) D_Choi + E_do co-primary**; **(iii) G2 (GNN-BP) included**.
> v2 key corrections (reviewer-1): **① the R̂ knob changed to non-unital CPTP (unital coherent ZZ is pinned at R=1 by the T-B theorem, cannot produce R̂>1) ② P2 changed to a coefficient-ratio criterion (the Petz residual is linear, not quadratic; K1 already falsified quadratic) ③ added a quantum-Markov-chain exact-recovery gate (replacing the cut 1D Petz-correctness calibration) ④ τ_D re-pinned below the bound ⑤ D_Choi entered the METRICS ledger ⑥ P4 weakened to sign + monotone, moved out of the GO gate**.
> Theory-first: the §5 prediction bands are frozen before any run; miss = finding, no widening of the tolerance after the fact.

---

## 0. Object and question (one sentence)

**Exact local windows (2×2) + principled gluing (Petz/BP) — can they reconstruct the exact global noise-channel object; where does it break as the bunching strength R̂ (= non-unital correlation) grows and the 2D seam becomes line-shaped — and is K1's ABSTAIN wall a wrong choice of gluing rule (mean-field) or a fundamental limit?**

- **Verdict object (information side)**: the **Choi state** J(E) of the noise-channel field E.
- **Capability-side object**: the **do()-ΔLER** through a **frozen decoder** (verifiable in the sandbox, §6 W1 note).
- ADR 0008 **C1 carrier-feasibility verdict**: M4's PROVISIONAL negative result → **a way out (GO)** or **a PROVISIONAL ceiling for this-teacher's correlation class (NO-GO)**. No "ran for nothing" branch.

---

## 1. Teacher (directly P2: 2D, fully exact, ≤15q)

### Geometry (m8 correction: honest re-scale)
**No exact-backend teacher with ≤15q can be a "complete surface code"** — even a d3 rotated surface is 17q > the 15q wall (the dataset note already proves it). Hence the teacher is **re-scaled to**:

> **A 12q two-dimensional nearest-neighbor lattice toy (3×4), with one defined logical string + a complete stabilizer subset** — the goal is not surface-faithfulness, but to **replicate the genuinely hard part of windowing a surface: 2D connectivity + line-shaped seams + an O(L) boundary penalty**.

Before freezing, pin down **in the registration text** (not only code+hash): the explicit stabilizer list, the `OBSERVABLE_INCLUDE` support, **and assert logical distance ≥2 with all checks complete (no dangling half-plaquette)** — otherwise LER/E_do is undefined. The exact layout is pinned in `cf_wr_teacher.py` + sha256, and the hash is inlined into the registration block (m11).

### Noise field (M1 correction: R̂ knob switched to non-unital CPTP)
Fully exact density-matrix simulation, holding the complete J(E) ground truth:
1. **Local marginal** — per-qubit single-qubit CPTP, r̂ ≈ 0.013, q̂_eff ≈ 0.014 (signed off in the N2 plan);
2. **R̂ knob (primary) = non-unital local CPTP field**, parameterized along the **registered T-B curve** by {p01,p10} (`D_package_derivations.md`: at r≈0.013, the Kraus members for R∈{2,5,17} are budgeted, R=5⇒(6.7039e-3, 1.20296e-1), the upper limit R≤1/(2r̂)≈39.4 covers the whole grid). **Never use unital coherent ZZ** (T-B theorem: unital-diagonal iid is pinned at R=1, cannot produce bunching). Non-unital CPTP is non-Pauli ⇒ stim cannot do it ⇒ **an exact density-matrix backend is still required** (the experiment's reason for existence is preserved).
3. **Coherent-edge knob φ (R-EDGE slot) = co-primary axis (amendment 2, owner decision b, 2026-06-14)** — apply a coherent `exp(−iφ Z⊗Z)` on the **seam-crossing edges**; **independent of R̂, carries no R̂**, but **co-constructs the primary field with R̂**: ρ becomes off-diagonal (genuinely quantum), so **the Petz rotation is actually exercised** — this is exactly the capability that distinguishes the density-matrix backend from classical DEM windowing. **Use the existing `forward/exact` backend (already validated for coherence by H1) + `apply_unitary`, do not introduce CUDA-Q** (12q does not need the scale tooling, and a new backend would break the exactness discipline; CUDA-Q is a d5/d7 carrier-level consideration, ADR 0008).

> **amendment 2 repositioning (2026-06-14, owner b):** φ was previously set as secondary — but the primary R̂ sweep **is classical** (a bit-flip keeps ρ diagonal, never exercising the backend's quantum capability), and a referee will ask "if it's classical, why use a density-matrix mechanism". Hence **φ is promoted to co-primary**: the primary reconstruction test is on (R̂, φ), and LER/E_do is changed to the **full-DM Born path** (`measure_parity_enumerate`; coherence breaks the classical-enumeration shortcut, it does not break the backend). bunching (R̂) and coherence (φ) remain **orthogonal**, but **both enter the primary field**; the φ=0 row is retained as the classical control.

---

## 2. Knobs and forced controls

- **Sweep R̂ ∈ {1, 2, 3, 5.3, 8, 12}** (realized via {p01,p10} along the T-B curve; **use the signed asymmetry δ′=p10−p01 as the perturbation coordinate**, both sides, δ′=0 an interior point — see derivation §3.2): **R̂=5.3 = the hardware-matched point (M3 P11), the core of the verdict**; {8,12} probe the collapse tail; {2,3} probe the monotone direction.
- **Sweep φ ∈ {0, 0.05, 0.10, 0.15} (amendment 2, co-primary)** — the coherent ZZ angle on the seam-crossing edges, covering K1 seam-test's φ∈[0.05,0.15]: **the primary reconstruction/GO point = (R̂≈5.3, φ*=0.10)** (hardware-matched bunching + a representative coherent edge); **the R̂ sweep is at φ*=0.10** (probing bunching collapse), **the φ sweep is at R̂≈5.3** (probing the P2 coefficient: the un-twirled coherent edge is leading-order **O(φ)**, derivation §2.4 governs; G0 slope-1, Petz-vs-mean-field). **The φ=0 row = the classical control** (reverts to the original classical bunching sweep). LER/E_do takes the full-DM Born path at φ≠0.
- **do() target + eval context pinned (C-1, for τ_E reproducibility)**: `do()` = single-edge error rate ×k (k, target edge, eval context pinned in `cf_wr_teacher.py` + inlined); ΔLER_true is computed by the frozen teacher → τ_E's absolute number is inlined at freeze time. **Substantive assertion (to prevent E_do from degenerating into measuring noise)**: the chosen do() must satisfy **|ΔLER_true| ≥ 5×floor** (otherwise τ_E=0.1×|ΔLER_true| degenerates); verify this lower bound on the teacher before freezing, and if it is not met, switch the do() target (before running any arm).
- **R̂=1 forced zero control = the unital point** (p01=p10), in the same context as P2.3: D(R=1)=g(r)+g(q)≈−7.43e-4 is **the marginal-term floor, not a seam residual** (C-2); the G1 reconstruction error must be ≤ the floor (§4 S-impl). A significant excess over the marginal floor ⇒ contamination ⇒ void and re-check, does not enter the verdict.
- **seed = 20260614**.

---

## 3. Gluing arms

| Arm | Rule | epistemic | Role |
|---|---|---|---|
| **G0** | mean-field/product gluing (= K1 `composed.py` usage) | (c) | zeroth-order rule — suspected K1 artifact |
| **G1** | **Petz recovery map** (JRSWW twirled universal form, depends only on ρ_BC), 2D boundary-MPS contraction | (a) construction + (b) error bound | **theoretically optimal, certified result** |
| **G2** | **GNN-learned BP**: detector-graph message-passing, **initialized at G1**, Markov-CMI regularized, **bounded by G1**, trusted only where consistent with G1 | (c) | tests "whether learned BP can withstand more correlation at the same cost"; does not touch G1's certified status |

**White-box core = per-window exact Born-NLL fit (LBFGS, ≤4q windows exact) + G1 Petz gluing.**
**A (optional warm-start)**: provides an initial value to the per-window LBFGS; **(a) gate (m7): the per-window fit must be bit-identical across initial values {cold init, A warm-start} (≤floor), otherwise A silently moves the "exact" fit, void A**.
G2 and A are tagged (c) throughout, anchored to the exact object, never entering the (a) trunk/premise (ADR 0008: a learned proxy has no exactness class).

---

## 4. Metrics (M4+M5 corrections)

### Entered into the ledger (M5, done)
- **D_Choi = per-seam reduced-block Choi–Jamiołkowski trace distance** (amendment 1): **row already added** to `docs/METRICS.md` Ledger (J_s=(I⊗E_s)|Ω⟩⟨Ω| on each seam's ≤6q support, the Choi block ≤2¹² dim feasible, the half-trace-norm ∈[0,1], the per-seam bound `√(I_nats)=√(ln2·I_bits)`); **the full 2²⁴ channel Choi is never materialized**, global = seam aggregate;
- **E_do does not create a new metric**: it maps to the **already-in-ledger** `knob_dler_error = |ΔLER_twin−ΔLER_teacher|` (absolute LER units, counterfactual-validity error) — this is exactly the field-standard metric for the carrier do()-fidelity against the teacher ground truth; the relative-% is only a **flagged project-defined secondary description**.

### Co-primary (owner ii; M4: declare each one's independent failure mode + drop the headline-S + re-pin τ_D)
| Metric | Object | The unique failure mode it captures | Threshold (c) |
|---|---|---|---|
| **D_Choi** = ½‖J_s−J_glue,s‖₁ (**per-seam reduced block**, amendment 1) | the reduced-channel Choi block (≤6q support, ≤2¹² dim) | **the full-channel reconstruction error, including directions the decoder cannot see** (per-seam) | τ_D = **0.5 × √(I_nats)** (the per-seam bound; **pinned below the bound** ⇒ passing τ_D implies the bound holds); GO uses the per-seam value at R̂≈5.3 |
| **E_do** = `knob_dler_error` = \|ΔLER_glue(do)−ΔLER_true(do)\| (absolute LER units, ledger metric) | do()-ΔLER | **the decision-relevant projection = the M4 transduction gap** (which Choi directions the decoder is insensitive to) | τ_E = **an absolute constant, = 0.1×\|ΔLER_true\|**, where ΔLER_true is computed by the **frozen teacher** (evaluator-side, with the do() target + eval context pinned in §2), **inlined as one absolute number at freeze time** (C-1: not glue-run data, hence reproducible, not a moving target) |

- **Why both are needed (non-redundant)**: E_do is the pushforward of J_glue through the frozen decoder, generally a function of D_Choi; **the two decouple only where the decoder is insensitive to the "specific glue-contaminated Choi direction"** — which is exactly **M4's lesson** (Choi/NLL win but the MWPM independent-edges DEM cannot see it). M4 is the empirical evidence that the two decouple.
- **GO = each one independently meets its threshold (AND gate)**; **drop the weighted headline S** (the AND gate is already the decision rule; averaging across incommensurable units has no decision effect and invites a "false equal-weighting" critique).

### Secondary (reported, not in the GO gate)
I_bits(A:C\|B)=S(AB)+S(BC)−S(B)−S(ABC) (von Neumann, bits) — order parameter, exact; LER absolute error; syndrome KL/TV (against the spacetime Markov length).

### Sanity gates (M3 correction: add a quantum-Markov-chain exact-recovery gate)
The cut 1D's "Petz-correctness" role: the old two gates **degenerate on the Petz mechanism** (at λ=0 Petz degenerates to the identity, never exercising the recovery rotation; with full windows there is no seam to glue) — the bug is invisible in both yet corrupts the 2D verdict. Add:
- **S-markov (new, core; C-4: the explicit construction is already pinned)**: one **explicit ≤4q quantum-Markov-chain point**, pinned in `cf_wr_teacher.py`, satisfying three assertions: **(1) I(A:C\|B)=0 to floor** (Petz theorem ⇒ G1 exact, D_Choi≤floor); **(2) D_Choi^{G0} ≥ 10×floor** (the G0 product must be inexact ⇒ the gate is non-empty, will not let a no-op Petz through); **(3) ρ_BC does not commute with ρ_B⊗I_C** (exercises the quantum rotation ⇒ catches transposed/wrong-order Petz-implementation bugs).
  - **worked baseline instance (proving (1)+(2))**: a 3q classical-Markov mixture ρ_ABC=½(|000⟩⟨000|+|111⟩⟨111|) (in A,B,C order): given B=b then A=C=b deterministically ⇒ I(A:C\|B)=0; but ρ_AC=½(|00⟩⟨00|+|11⟩⟨11|)≠ρ_A⊗ρ_C ⇒ ρ_AC−ρ_A⊗ρ_C=diag(¼,−¼,−¼,¼), trace norm=1 ⇒ **D_Choi^{G0}=½‖·‖₁=½>0** (≥10×floor ✓). Petz reconstructs exactly from ρ_AB, ρ_BC.
  - **non-commuting companion (satisfies (3), catches the rotation bug)**: apply a fixed conjugating-basis local unitary on each of A and C so that ρ_BC is off-diagonal ⇒ the rotated-Petz [·]^{(1±it)/2} is genuinely exercised.
  **The minimal replacement for the cut 1D; must pass all three assertions before freezing**.
- **S-impl**: D_Choi of G1@R̂=1 ≤ 1e-3 (doubles as implementation + zero control);
- **S-trivial**: window = full fragment ⇒ D_Choi ≤ floor (recover+score identity);
- **S-monotone**: D_Choi is monotone non-decreasing in R̂.

---

## 5. Theory-first prediction bands (frozen before the run, (b), miss=finding)

- **P1**: sub-threshold G1 D_Choi ∝ exp(−w/2ξ(R̂)); fit ξ(R̂) to confirm the log-linear collapse.
- **P2 (core bet, M2 correction: coefficient ratio, not slope; the (a)-basis derivation is complete → `docs/cf_wr/P2_derivation.md`)**:
  - **P2.1 (a)**: `D_Choi^{G0} = c_{G0}·λ + O(λ²)`, **slope 1** (band [0.90,1.10]; K1 measured 0.973, retro-confirmed). **Theorized**: what the G0 product constraint drops is the **first-order connected correlation** χ⁽¹⁾ (non-unital ⇒ χ⁽¹⁾≠0), c_{G0}=½‖χ⁽¹⁾‖₁. unital/twirled point ⇒ slope 2 (parity).
  - **P2.2 (b) independent conclusion (not a GO premise) = coefficient ratio**: `D_Choi^{G1}=c_{G1}·λ+O(λ²)`, the bet is **c≡c_{G1}/c_{G0} < 1 (direction c ≤ 0.5)**. **Fully (b)**: ruling B-1 holds that `c<1` is **not an (a)-theorem** — `‖χ−Petz(χ)‖₁<‖χ‖₁` does not hold in general (the trace norm is not aligned-subtractive; rotated-Petz can over-rotate; if χ⁽¹⁾ has no ρ_BC support then c=1). **c≥1 = finding (Petz does not win), c<1 = supports the artifact narrative, c≈0 (G1 slope≈2) = bonus**. **Decoupled from GO** (§6): GO does not take c<1 as a premise. A within-run comparison ⇒ c is more robust than either slope alone. **Drop v1's "G1 slope ≥1.8"** (Petz O(λ²) is not provable for a non-unital interface).
  - **P2.3 (a) pin**: at the unital point (p01=p10) both c_{G0} and c_{G1} go to 0 at first order, residual O(λ²). A violation = build bug.
- **P3**: threshold ξ(R̂*)/w = 1 ± 0.3; crossing it crashes both arms.
- **P4 (2D, B-3 correction: at-most-linear, not strictly linear, not √L)**: G1 per-seam D_Choi is **monotone non-decreasing + sub-additively upper-bounded O(L) (a)** in seam-length L; **linear is the (b) centre** (exponent band [0.85,1.15]). **Derivation**: the seam cells of adjacent 2×2 windows **share a corner qubit ⇒ supports intersect ⇒ the trace norm is sub-additive** (`‖ΣAℓ‖₁≤Σ‖Aℓ‖₁`), so only a ≤c·L upper bound is possible, ∝L cannot be asserted (corner contributions may partly cancel ⇒ possibly sub-linear); **√L is a fluctuation law, not applicable to the L₁ Choi residual**. Honest caveat: the exact-DM oracle only reaches L∈{1,2,3}, so **only sign+monotone is measurable**, the L-exponent is direction-only. **P4 is not in the §6 GO gate**. **c (P2.2) is L-independent at first order ⇒ c<1 is a robust 2D-transferable conclusion**; the absolute-residual L-law is direction-only.
- **P5 (G2)**: at R̂≤5.3, \|D_Choi^{G2}−D_Choi^{G1}\| ≤ τ_agree; at R̂≥8 it may extend the reach (exploration, not a bet).
- **Zero control**: G1@R̂=1 ≤ floor (= S-impl).

---

## 6. GO / NO-GO (M4+m9+m10 corrections)

**W1 note (airtight)**: E_do is **verifiable inside the sandbox (teacher)** — the teacher has a re-runnable ground truth, the counterfactual is realizable; it verifies the **carrier do()-fidelity against the teacher ground truth**, **not** a hardware do() claim (hardware W1 is blocked). **No number, band, or routing in this registration is ever cross-read to hardware** (aligned with the claim-scope section of K1 results).

| Verdict | Condition (R̂≈5.3, G1) | Meaning |
|---|---|---|
| **GO (carrier feasible)** | D_Choi ≤ τ_D **and** E_do ≤ τ_E (R̂≈5.3, G1) — **pure absolute reconstruction quality, does not include c<1** (B-1: c<1 is a (b) result, not an (a) premise, does not enter the GO gate) | **the carrier reconstructs successfully against the ground truth at the hardware-matched correlation** ⇒ ADR 0008 C1 goes ahead; the dMLE-TN bulk + window-exact CPTP seam-slot path is open. **If P2.2 simultaneously measures c<1** (an independent (b) conclusion) ⇒ further supports "M4's failure = a mean-field/independent-edges-format artifact, K1 should re-measure with Petz"; c<1 and GO are decoupled, reported separately |
| **NO-GO (a PROVISIONAL ceiling for this-teacher's correlation class)** | even with G1 Petz, at R̂≈5.3 D_Choi/E_do still exceeds the threshold | windowing cannot save this correlation class ⇒ must switch to a scalable representation (Tsim/LPDO) or accept a format ceiling. **But**: **NO-GO is not theorem-grade** (M1's teacher correlation class is finite, the Petz-bug risk must first be ruled out via S-markov) — **it does not override K1's second read, does not promote M4 to a theorem, it is just one more (b)/(c)-level data point** |
| **MIXED** | the Choi and do() criteria disagree / pass but the collapse tail is too early | report ξ* and the boundary-penalty scaling, route to "windowing is bounded-feasible at ξ<ξ*" |

**GO/NO-GO defaults to PROVISIONAL**, unless upgraded to theorem-grade; nothing is built on it (no definitions/designs).

**Reporting discipline (to prevent "a good result ≠ a real capability", owner 2026-06-14):**
- **Raw numbers before the gate**: RESULTS must put the **absolute D_Choi(R̂) curve, ξ*, and the raw value of c** first; **GO/NO-GO is only a derived label, not the headline number**.
- **τ_D is half of a loose upper bound**: √(I_nats) is an upper bound and itself loose, so "D_Choi ≤ τ_D" is **necessary not sufficient**; the report must state explicitly that "passing the gate" does not equal "reconstructs well", the genuine quality is read from the absolute D_Choi and c.
- **The bounded meaning of GO is pinned**: a GO on the 12q toy **only proves "the gluing mechanics + error law are correct where verifiable"**, it **does not prove that the d5/d7 carrier works** (the toy lacks the long-boundary O(L) penalty + lacks real hardware's unrepresentable quality / model-class mismatch); every GO conclusion must carry this bounded statement, must not be cross-read to scale or hardware.

---

## 7. Feasibility / cost

12q density matrix 2¹²×2¹² ~16.8M complex elements; CMI/Petz on ≤4q marginals is small linear algebra ⇒ **minutes-scale**; **pure sim/teacher side, zero real hardware, zero held-out (05–09), zero escrow (15–19) touched, exactness preserved throughout**; GPU runs the exact evolution + Choi (GPU-only model compute); 65GB memguard; scripted-execution.

---

## 8. Freeze / build sequence (theory-first)

1. **This v2 → reviewer-2 pass** (read-only; re-review: faithfulness of the T-B knob parameterization, whether the leading-order derivation of the Petz residual is written in, the exactness of the S-markov gate, whether τ_D is genuinely below the bound, the 12q toy's logical distance ≥2, all frozen constants inlined);
2. **The two (a) bases are filled in**: (α) the leading-order derivation of the Petz residual = `docs/cf_wr/P2_derivation.md` (✓); (β) the METRICS.md Choi-trace-distance row is added + E_do is mapped to the ledger's `knob_dler_error` (✓);
3. fold into `docs/metric_results.md` as `### CF-WR PRE-REGISTRATION` (frozen, inlining all τ / ratio bands / R̂ grid / seed / teacher-sha256);
4. **4 scripts, each ≥3 sub-agents + reviewer, serial**: `cf_wr_{teacher,windows,glue,score}.py` (assertions + printed evidence + flush + spawn `__main__` guard);
5. run (seed 20260614, sim-only) → `### CF-WR RESULTS` + metric audit + rigor audit (all (a)/(b)/(c) tagged, theorem-backed vs PROVISIONAL).

---

## 9. Red lines (a breach of any one is an incident)

- **sim/teacher-only**: do not touch real hardware, held-out 05–09, escrow 15–19;
- **exactness preserved**: white-box core = exact Born-NLL + G1 Petz; G2/A tagged (c), anchored to the exact object, never entering the (a) trunk/premise/derivation basis;
- **registration text frozen**: τ_D=0.5×√CMI-bound, τ_E=10%, the P2 coefficient ratio c<1, the R̂ grid, the seed, the teacher hash all inlined and pinned; miss=finding, no widening of the tolerance after the fact;
- **R̂ knob = non-unital T-B CPTP** (never unital coherent ZZ); **the φ coherent knob is independent, carries no R̂**;
- **conclusion discipline**: GO/NO-GO defaults to PROVISIONAL; NO-GO is not theorem-grade;
- **theory-first**: the §5 prediction bands + the Petz leading-order derivation are frozen before the run;
- **scripted-execution + 65GB memguard + GPU-only model compute**;
- git: commit on completion (no push, no co-author).
