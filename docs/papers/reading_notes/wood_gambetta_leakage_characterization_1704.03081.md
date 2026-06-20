# Deep review — Wood & Gambetta, Quantification and Characterization of Leakage Errors

> Deep reading note (academic-paper-review format; full read Secs. I–VI + Appendices
> A–E, Figs. 1–6). This is the **canonical leakage-metric paper** — the source of the
> leakage rate `L1`, seepage rate `L2`, coherence-of-leakage `C_L`, and the bounds that
> let us **define and bound a leakage-approximation error against an exact qutrit
> reference**. **Relevance to our SIM-only non-Pauli teacher** is the centerpiece. The
> superoperator / Lindblad algebra I take as correct (standard open-systems lineage),
> not re-derived.

## Metadata
- **Authors.** Christopher J. Wood, Jay M. Gambetta (IBM T. J. Watson Research Center).
- **arXiv / venue / status.** arXiv:1704.03081v1 [quant-ph], 10 Apr 2017; published as
  **Phys. Rev. A 97, 032306 (2018)**. Peer-reviewed.
- **Domain / type.** Quantum error characterization; **framework + protocol + simulation**
  (metric definitions, a leakage-RB estimation protocol, transmon Lindblad simulation,
  five worked noise models). Decrypted source PDF: `docs/papers/wood_1704.03081_decrypted.pdf`
  (the shipped `wood_gambetta_leakage_characterization_1704.03081.pdf` is password-locked;
  pikepdf re-save + pymupdf text/figure extraction under `docs/papers/.wood_pages/`).
- **Page map (the 19-page PDF).** Sec. II metrics (pp. 2–3); Sec. III LRB protocol +
  transmon simulation, Figs. 1–3 (pp. 3–8); Sec. IV coherent leakage, Props. 1–2 (pp. 6–8);
  Sec. V five noise models (DLE/DLM, unitary, Lindblad/thermal, multi-subspace), Figs. 4–6
  (pp. 8–13); Sec. VI conclusion (p. 13); Appendices A–E with all derivations (pp. 15–19).

## TL;DR
A quantum system whose qubit lives in a subspace `X_1` of a larger space `X = X_1 ⊕ X_2`
can **leak** population into `X_2` and **seep** it back. Wood–Gambetta give the field's
canonical, architecture-independent metrics for this: **state leakage** `L(ρ) = Tr[Π_2 ρ]`
(Eq. 1), and for a CPTP error channel `E` the **leakage rate** `L_1(E) = L(E(Π_1/d_1))`
(population lost from the computational subspace, averaged over input states) and the
**seepage rate** `L_2(E) = 1 − L(E(Π_2/d_2))` (population returned) (Eq. 2). Two rates,
not one, are required: their ratio depends entirely on the physical mechanism (erasure
`L_2=0`; thermal `L_2 ≫ L_1`; unital/unitary `d_1 L_1 = d_2 L_2`, Eq. 51-footnote [26]).
They then separate **incoherent** leakage (the only part the metrics above see) from
**coherent** leakage (superpositions *across* the `X_1`/`X_2` cut), define the
**coherence of leakage** `C_L(ρ) = ‖P_C(ρ)‖_1` (Eq. 31) with the tight bound
`C_L(ρ) ≤ 2√(p_l(1−p_l))` (Prop. 1, saturated for pure states), and the channel-level
**coherent leakage/seepage rates** `C_{L1}, C_{L2}` bounded by `C_{Lj} ≤ 2√(L_j(1−L_j))`
(Prop. 2). A modified randomized-benchmarking protocol (**LRB**, Sec. III) estimates
`(L_1, L_2, F)` from a **single-exponential** decay `p_{Π1}(m) = A + B λ_1^m` with
`L_1 = (1−A)(1−λ_1)`, `L_2 = A(1−λ_1)`, `λ_1 = 1 − L_1 − L_2` (Eqs. 9–14). Five worked
models — erasure, depolarizing-leakage extension (DLE) / depolarizing-leakage model (DLM),
unitary `|1⟩↔|2⟩` Rabi leakage, simple dissipative, and thermal-relaxation — give
closed-form `L_1, L_2`, including the **qutrit thermal** result
`L_1 ≈ κ n̄ Δt`, `L_2 ≈ 2(1+n̄)κΔt/d_2` ⇒ `L_2 ≫ L_1` at low `n̄` (Eqs. 78–79).

The relevance to us is direct and load-bearing. (a) **Canonical model:** our
`|1⟩→|2⟩` leakage + seepage teacher is exactly their unitary-leakage (Eqs. 55–58) and
dissipative-leakage (Eqs. 70–73, 74–79) models, parameterized by the *same* two rates
`L_1, L_2` plus a coherence axis `C_L`. (b) **Bounding an approximation:** their
**leakage-accumulation model** (Lemma 1) gives the exact `L(E_L^m(ρ))` for the
depolarizing (incoherent) extension, and **Fig. 4** quantifies the error of the
incoherent (Pauli/leakage-reset) approximation against the exact unitary qutrit — *this
is the template for our "leakage-approximation error vs exact qutrit reference."* The
coherence-of-leakage 1-norm `‖P_C(ρ)‖_1` and Props. 1–2 are the **metric** in which that
error is honest. (c) **Additivity:** Lemma 2 (Eq. 69) says unitary and dissipative
leakage rates are **additive to second order in Δt** when the dissipators are pure
ladder operators — the discretization lemma that lets a Trotterized leakage teacher
compose `T1/T2 + control-leakage` per gate slice without cross-terms to leading order.

## Main contribution + core method (full technical detail)

### 1. The subspace model and the two rates (Sec. II)
The system is split into a `d_1`-dimensional **computational subspace** `X_1` (ideal
dynamics) and a `d_2`-dimensional **leakage subspace** `X_2`, with `X = X_1 ⊕ X_2` and
orthogonal projectors `Π_1, Π_2` (`𝟙_1, 𝟙_2` in the paper). **State leakage** of a
density matrix is

  `L(ρ) = Tr[Π_2 ρ] = 1 − Tr[Π_1 ρ]`  (Eq. 1)

A **leakage error** is any CPTP map `E` that couples `X_1 ↔ X_2`. Because a channel can
both push population out and pull it back, two averaged rates are needed (Eq. 2):

  `L_1(E) = ∫ dψ_1 L(E(|ψ_1⟩⟨ψ_1|)) = L(E(Π_1/d_1))`   — **leakage rate** (out of `X_1`)
  `L_2(E) = 1 − ∫ dψ_2 L(E(|ψ_2⟩⟨ψ_2|)) = 1 − L(E(Π_2/d_2))` — **seepage rate** (back into `X_1`)

The averages are Haar averages over states in `X_1` (resp. `X_2`). Worst-case rates are
bounded by the averages: `d_1 L_1 ≥ L(E(ρ_1))`, `d_2 L_2 ≥ 1 − L(E(ρ_2))` (Eqs. 3–4).
Gate fidelity is redefined to average **only over `X_1`** (Eq. 6) and decomposes as

  `F(E) = (d_1 F_pro(E) + 1 − L_1)/(d_1 + 1)`,  `F_pro(E) = Tr[(Π_1⊗Π_1) S_E]/d_1²`  (Eqs. 7–8)

where `S_E` is the superoperator. The headline conceptual claim: **`(L_1, L_2, F)` are
the three numbers that characterize a gate under leakage**, and `L_1+L_2` alone (the
prior "coherence of leakage" of Ref. [18]) is insufficient and is a *misnomer* — leakage
and seepage arise even from purely incoherent thermal relaxation. The `L_1:L_2` ratio is
mechanism-diagnostic (Sec. II, p. 3):
- **Erasure:** `L_2 = 0` (leaked population irretrievably lost).
- **Thermal relaxation:** `L_2 ≫ L_1` when `X_1` is the low-energy subspace.
- **Unital / unitary:** `d_1 L_1 = d_2 L_2` (footnote [26]: from `Tr[Π_2 E(𝟙)] = d_2` when `E` is unital).

### 2. LRB — estimating `(L_1, L_2, F)` from a single-exponential decay (Sec. III, App. A)
LRB modifies standard Clifford randomized benchmarking. Requirements: a 2-design on
`X_1` (Cliffords) and the ability to estimate populations of `X_1` basis states. The
protocol (Sec. III, steps 1–8):
1. Random length-`m` Clifford sequence + the RB recovery `C_{m+1}`.
2. Prepare `|0⟩⟨0|`, apply the sequence, measure `p_j(i'_m) = Tr[M_j i'_m(ρ_0)]`.
3. Sum to get the `X_1` population `p_{Π1}(i'_m) = Σ_j p_j`.
4–5. Average over `K` random sequences and several lengths `m`.
6. Fit the **single exponential** `p_{Π1}(m) = A + B λ_1^m` (Eq. 9), then
   `L_1 = (1−A)(1−λ_1)`, `L_2 = A(1−λ_1)`, with `A ≈ L_2/(L_1+L_2)`,
   `B ≈ L_1/(L_1+L_2) + ε_spam`, `λ_1 = 1 − L_1 − L_2` (Eqs. 10–14).
7–8. Fit `p_0(m) = A_0 + B_0 λ_1^m + C_0 λ_2^m` (the fidelity curve) with `λ_2 = (1−p_l)μ_1`
   to extract `F` (Eqs. 15–16).

The decay-model derivation (App. A) is the technical core. Twirling the Clifford group on
`X_1` is a 2-design, so `E[S_{V1,k} S_E S_{V1,k}^†] = W_1(E) = μ_1 I_1 + (1−μ_1) D_1` with
`μ_1 = (d_1 F_{E11} − 1)/(d_1 − 1)` (Eqs. A11–A13). **The single key assumption** is
**Assumption 4 (Eq. A16):** the Clifford twirl on `X_1` *also* fully depolarizes `X_2`
(the leakage-subspace unitaries `{U_{2,k}}` form a 1-design). Under it the averaged
sequence superoperator collapses to a power of one effective channel:

  `E_{i'_m}[S_{i'_m}] = S_E S_{E_D}^m`,
  `E_D = (1−L_1)(μ_1 I_1 + (1−μ_1) D_1) + L_1 D_{21} + L_2 D_{12} + (1−L_2) D_2`  (Eq. A18)

`D_{ij}(ρ) = Tr[Π_j ρ] Π_i/d_i` is the completely depolarizing map `X_j → X_i` (Eq. A19).
The leakage block is a `2×2` stochastic matrix whose `m`-th power is closed-form (Eq. A20),
giving the **leakage accumulation** result. Including a SPAM/measurement-leakage model
`Σ_j M_j = (1−q_1)Π_1 + q_2 Π_2` (Eq. A29) yields the final `A, B` with error terms
`ε_M = q_1 + p_l(1−q_1−q_2)` and `ε_Q = L_1 q_2 − L_2 q_1` (Eqs. A33–A35) and a variance
`Var(L_j^est) = ε_Q²` — i.e. **estimating from `A` is more robust than from `B`** (App. A,
final line). This single-exponential model is the property that distinguishes LRB from the
bi-/multi-exponential prior proposals [23, 24] and the `L_1+L_2`-only proposal [18].

### 3. Coherent leakage — the metric that survives our approximation (Sec. IV, Apps. B–C)
The Sec. II metrics see only *populations* and are blind to **coherences across the
`X_1`/`X_2` cut**. Wood–Gambetta partition the channel/state space accordingly:
- **Incoherent leakage subspace (ILS):** states `ρ = (1−p_l)ρ_1 + p_l ρ_2` (block-diagonal).
  Projector (a CPTP map) `P_I(ρ) = Π_1 ρ Π_1 + Π_2 ρ Π_2` (Eqs. 27–28).
- **Coherent leakage subspace (CLS):** the traceless off-diagonal blocks. Projector
  `P_C = I − P_I`, `P_C(ρ) = Π_1 ρ Π_2 + Π_2 ρ Π_1` (Eqs. 29–30).

The **coherence of leakage** of a state is the 1-norm of the off-diagonal part:

  `C_L(ρ) = ‖P_C(ρ)‖_1 = ‖ρ − P_I(ρ)‖_1`  (Eq. 31)

The 1-norm is chosen for an operational (Helstrom-distinguishability) reading. For a pure
state `|ψ⟩ = √(1−p_l)|ψ_1⟩ + √p_l|ψ_2⟩` with leakage `p_l`,

  `‖P_C(|ψ⟩⟨ψ|)‖_1 = 2 √(p_l(1 − p_l))`  (Eq. 34), maximal (=1) at `p_l = 1/2`.

**Proposition 1 (App. B):** for *any* state, `C_L(ρ) ≤ 2√(p_l(1−p_l))` with `p_l = L(ρ)`,
saturated for pure states. (Proof: spectral decomposition + triangle inequality +
concavity of `√x` + convexity of `x²`.) At the channel level the **coherent leakage rate**
and **coherent seepage rate** are the CLS analogues of `L_1, L_2` (Eqs. 39–40):

  `C_{L1}(E) = ∫ dψ_1 C_L(E(|ψ_1⟩⟨ψ_1|))`,   `C_{L2}(E) = ∫ dψ_2 C_L(E(|ψ_2⟩⟨ψ_2|))`

**Proposition 2 (App. C):** `C_{Lj}(E) ≤ 2√(L_j(1−L_j))`, `j = 1,2`. (Proof via Prop. 1
applied to outputs + the `n=2` Haar twirl `∫ dψ_1 |ψ_1⟩⟨ψ_1|^{⊗2} = (Π_1⊗Π_1 + SWAP)/(d_1(d_1+1))`,
Eqs. C7–C12.) These two bounds are the workhorses for us: **they bound a quantity that
cannot be measured from `X_1` alone (coherence) by quantities that can (`L_1, L_2`).** The
channel decomposition that underpins this is `E = P_I E P_I + P_I E P_C + P_C E P_I + P_C E P_C`
(Eq. 35); only the first term `E_I = P_I E P_I` is trace-preserving and carries the leakage
block `E_I = (1−L_1)E_{11} + L_1 E_{21} + L_2 E_{12} + (1−L_2)E_{22}` (Eqs. 36–37) that LRB
estimates. The remaining three terms are exactly the **coherence the incoherent
approximation discards**.

### 4. Five leakage models, with closed-form rates (Sec. V, Apps. D–E)
- **(A.1) Erasure** `E(ρ) = (1−p_l)ρ + p_l|ψ_2⟩⟨ψ_2|`: `L_1 = p_l`, `L_2 = 0`; after `m`
  applications `L(E^{∘m}(ρ)) = 1 − (1−p_l)^m` (Eqs. 42–43).
- **(A.2) Depolarizing-leakage extension (DLE)** of a computational channel `E_1`:
  `E_L = (1−L_1)E_1 + L_1 D_{21} + L_2 D_{12} + (1−L_2)D_2` (Eq. 44). Purely **incoherent**
  — it keeps only `(L_1, L_2)` and removes all coherence/memory. **Lemma 1 (App. D)** —
  the **leakage accumulation model**:

    `L(E_L^m(ρ)) = L_1/(L_1+L_2) − (L_1/(L_1+L_2) − p_l)(1 − L_1 − L_2)^m`

  independent of `E_1`'s in-subspace dynamics; steady-state `L_1/(L_1+L_2)`. (Proof:
  the leakage block is a `2×2` stochastic matrix, Eqs. D1–D3.)
- **(A.3) Depolarizing-leakage model (DLM)** = DLE with `E_1` itself depolarizing (Eq. 46);
  constructible from any `E` by a 2-design twirl on `X_1` + 1-design depolarize on `X_2`
  (Eqs. 47–50), preserving `F, L_1, L_2` exactly (Eqs. 51–53). This is the *ideal target
  LRB twirls an arbitrary channel into*; its fidelity decay (Eq. 54) is the LRB model.
- **(B) Unitary leakage** — exchange `H = ½(|1⟩⟨2| + |2⟩⟨1|)` (Eq. 55), `U = e^{-itH}`
  (Eq. 56). State leakage and channel rates **oscillate**: `L(ρ_1(t)) = sin²(t/2)⟨1|ρ_1|1⟩`
  (Eq. 57), `L_j(U(t)) = (1/d_j) sin²(t/2)` (Eq. 58), with `d_2 L_2 = d_1 L_1`. Coherent
  leakage `C_L(ρ_1(t)) = |sin t|` (Eq. 59), with `C_{L1}` given exactly (Eq. 60) and
  bounded by Prop. 2 (Eq. 61). The DLM projection of this unitary error (Eqs. 62) **kills
  the oscillation** and gives an exponential; an *imperfect* twirl (leakage-subspace
  depolarizing strength `p`, Eq. 63) leaves residual oscillations — **Fig. 4**.
- **(C) Lindblad leakage** `E = e^{t(H+D)}`, `D(ρ) = Σ_k γ_k(A_k ρ A_k^† − ½{A_k^† A_k, ρ})`
  (Eqs. 67–68). **Lemma 2 (App. E):** if the dissipators are pure raising/lowering ladder
  operators `A_{±k} = Σ_j α_j|j±k⟩⟨j|`, then **to second order in Δt the leakage and
  seepage rates are additive**: `L_j(E) = L_j(E_uni) + L_j(E_diss)` (Eq. 69). (Proof: the
  cross term `⟨⟨Π_2|(DH + HD)|Π_1⟩⟩ = 0` because the relevant traces are real and cancel,
  Eqs. E1–E4.)
  - **(C.1) Simple dissipative** `A_{21}=|2⟩⟨1|` (rate `γ_1`), `A_{12}=|1⟩⟨2|` (rate `γ_2`):
    `L_1(E) = γ_1/(d_1(γ_1+γ_2)) · (1−e^{-t(γ_1+γ_2)})`, `L_2(E) = γ_2/(d_2(γ_1+γ_2)) · (1−e^{-t(γ_1+γ_2)})`
    (Eqs. 71–72), and the full state-leakage trajectory (Eq. 73).
  - **(C.2) Thermal relaxation** (photon-loss `D_c = κ(1+n̄)D[a] + κn̄ D[a†]`, Eqs. 74–75,
    `κ = γ_↓ − γ_↑`, `n̄ = γ_↑/(γ_↓−γ_↑)`, Eq. 76). Equilibrium leakage
    `L(ρ_eq) = (γ_↑/γ_↓)² = (n̄/(1+n̄))²` (Eq. 77). For `κΔt ≪ 1`, to second order:
    `L_1(E) ≈ κ n̄ Δt[1 − (3+4n̄)κΔt]`, `L_2(E) ≈ (2(1+n̄)κΔt/d_2)[1 + (1−4n̄)κΔt]`
    (Eqs. 78–79) ⇒ **`L_2 ≫ L_1` at low `n̄`** (Fig. 6). For a cavity `d_2 = ∞`; at low
    `n̄` truncate to a **qutrit** (`d_2 = 1`); the rates match transmon `n̄ ∈ [10^{-2}, 10^{-1}]`.
- **(D) Multiple leakage subspaces** (Sec. V D): decompose `X_2 = Y_1 ⊕ … ⊕ Y_m` and define
  per-subspace `L_{Y_j}, L_{1Y_j}, L_{2Y_j}` (Eqs. 81–83) with `L = Σ L_{Y_j}`, `L_1 = Σ L_{1Y_j}`,
  `L_2 = Σ d_{2j} L_{2Y_j}` (Eqs. 84–86). The 2-qubit example: `Y_1` = qubit-1 leaks, `Y_2`
  = qubit-2 leaks, `Y_3` = both leak (Eqs. 87–89) — the **per-qubit leakage bookkeeping** a
  multi-qubit surface-code leakage teacher needs.

## Key results (figures and tables)
- **Fig. 1 (p. 5) — transmon LRB validation.** Average gate infidelity `1−F` (top),
  leakage rate `L_1` (middle), seepage rate `L_2` (bottom) vs `X_{90}` gate time (8–30 ns)
  for four pulse types: GAUSS (`α=0`), DRAG-F (`α≈0.5`, fidelity-optimized), DRAG-L (`α≈1`,
  leakage-optimized), DRAG-Z (DRAG-L + Z-frame corrections), with the pure-`T1` limit.
  Fitted LRB estimates (points, with 95% CI shading) agree with theory (solid lines from
  the simulated superoperators). Takeaways: `L_1` is **1–2 orders of magnitude below `1−F`**;
  the **dominant gate error is a leakage-induced phase error**, not the leakage rate itself,
  so DRAG-L (which suppresses `L_1`) barely beats GAUSS in fidelity while DRAG-F/DRAG-Z win;
  **seepage `L_2` is completely dominated by thermal `T1` seepage**.
- **Fig. 2 (p. 6) — estimator convergence.** Fitted `1−F`, `L_1`, `L_2` (16 ns pulse) vs
  number of averaged random Clifford sequences (seeds), with 95% CI shrinking — shows the
  single-exponential fit converges and quantifies the seed budget.
- **Fig. 3 (p. 7) — example LRB decay data.** `p_0` (top, the usual RB `|0⟩` curve) and
  `p_{Π1}` (bottom, the `X_1`-trace curve) for 8/14/30 ns pulses. The **8 ns** (largest-`L_1`)
  `p_{Π1}` curve visibly **oscillates** — the diagnostic signature of insufficient
  leakage-subspace twirling (Assumption 4 partially failing), i.e. residual coherent leakage.
- **Fig. 4 (p. 11) — leakage accumulation, ideal vs imperfect twirl.** State leakage
  `L(E^m)` vs number of imperfect-DLM applications for leakage-subspace depolarizing
  strengths `p = 0, 0.01, 0.1, 1`. `p=0` (no leakage-subspace depolarization) shows large
  coherent **oscillations**; `p=0.1` damps them but still accumulates faster than ideal;
  the **black dotted curve is the perfect-DLM exponential** (Lemma 1). **This figure is the
  exact "approximation-error vs reference" picture we need** (Sec. "useful", item 2): the
  incoherent (depolarized) model is a *lower bound* on/biased estimate of the true coherent
  leakage accumulation, and the gap is the coherent contribution `C_L`. Overestimate of
  `L_1` results if oscillations are read as decay: the ideal rate is `L_1 = ½ sin²(Δt/2)`.
- **Fig. 5 (p. 11) — first-order unitary leakage.** First-order Dyson leakage rate (Eq. 66,
  `L_j ≈ (t²/d_j) Tr[Π_2 H̄ Π_1 H̄]`) for an `X_{-π/2}` pulse vs pulse length, anharmonicity
  `δ/2π = −300 MHz`, for GAUSS / DRAG-F / DRAG-L. DRAG-L's first-order leakage is **0** (off
  the log plot) — the analytic basis for DRAG leakage suppression.
- **Fig. 6 (p. 12) — thermal leakage vs seepage.** `L_1` (solid) and `L_2` (dashed) vs
  equilibrium photon number `n̄ ∈ [0, 0.1]` for `κΔt = 10^{-4}, 10^{-3}, 10^{-2}` (qubit in
  the lowest two cavity levels). Confirms **`L_1 ≪ L_2`** across the range (Eqs. 78–79) — the
  thermal-leakage asymmetry our `T1` teacher must reproduce.

(No tables; the paper's quantitative content is in the equations and Figs. 1–6.)

## **Useful for our project**

Our program: a **SIM-only teacher** generates realistic-noise surface-code **syndrome**
data with **non-Pauli** mechanisms (`T1/T2`, **leakage `|1⟩→|2⟩` + seepage**, soft IQ
readout) to train a decoder; the headroom over Pauli decoders (MWPM / TN-MLD / Google
RL-prior) is the non-Pauli signal. This paper is the **canonical leakage model** and, more
than any other we hold, supplies (a) the model + parameterization, (b) the error metric
for bounding an approximation, and (c) the additivity result that licenses a Trotterized
teacher. Concretely:

1. **The leakage teacher's parameters and definitions are this paper's (Eqs. 1–2, 55–58,
   70–79).** Parameterize the SIM leakage channel by the **two rates** `(L_1, L_2)` — never
   one combined rate (Sec. II, p. 3 is explicit that `L_1+L_2` is insufficient and a
   misnomer). For a transmon-faithful surface-code teacher:
   - **Control/coherent leakage** = the **unitary-leakage** model (Eqs. 55–58):
     `|1⟩↔|2⟩` exchange with `L_j = (1/d_j)sin²(t/2)`, generating **oscillating** leakage
     and nonzero coherence `C_L = |sin t|` (Eq. 59). This is the **dominant non-Pauli signal**
     the prompt targets and the part Pauli/erasure decoders cannot see.
   - **Thermal/incoherent leakage** = the **photon-loss / thermal-relaxation** model
     (Eqs. 74–79): `L_1 ≈ κ n̄ Δt`, `L_2 ≈ 2(1+n̄)κΔt/d_2`, with **`L_2 ≫ L_1`** at the
     transmon `n̄ ∈ [10^{-2},10^{-1}]` (Fig. 6). Our canonical `T1/T2` Kraus channels are the
     *in-subspace* part; this is the *leakage* part. The qutrit truncation `d_2 = 1` at low
     `n̄` is sanctioned in-text (p. 13) — i.e. **one extra `|2⟩` level per data qubit is the
     paper-endorsed minimal leakage sim**.
   - **Per-qubit / multi-subspace bookkeeping** (Eqs. 80–89): the surface-code teacher needs
     leakage rates *per data qubit* (and cross-qubit `Y_3` if modeled); Sec. V D gives the
     exact `L_1 = Σ_j L_{1Y_j}` decomposition. (Caveat: Sec. V D explicitly *ignores direct
     interactions between leakage subspaces* — see Limitations.)

2. **Bounding our leakage-approximation error against an exact qutrit reference — the
   central methodological deliverable.** Any scalable leakage sim that is *not* a full
   qutrit density-matrix evolution (e.g. a **Pauli-twirled / leakage-as-erasure-reset /
   DLM** approximation, which is what lets leakage drop into a Stim-style or DEM carrier)
   discards exactly the **CLS** part of the channel (`P_I E P_C + P_C E P_I + P_C E P_C`,
   Eq. 35). This paper gives **both** the right reference object and the right metric:
   - **Reference object:** the exact unitary/Lindblad qutrit channel (Eqs. 56, 64, 67–68),
     and its **leakage-accumulation trajectory** `L(E^m(ρ))` (Lemma 1 / Eqs. 57, 62, 71–73).
   - **Approximation:** its **DLE/DLM** incoherent projection (Eqs. 44, 46; constructed by
     Eq. 47), which by Lemma 1 has the closed-form accumulation
     `L(E_L^m(ρ)) = L_1/(L_1+L_2) − (L_1/(L_1+L_2) − p_l)(1−L_1−L_2)^m`.
   - **Error metric:** the **coherence of leakage** `C_L = ‖P_C(ρ)‖_1` (Eq. 31), with the
     **certified bound** `‖our_approx − exact‖` controlled by
     `C_L(ρ) ≤ 2√(p_l(1−p_l))` (Prop. 1) at the state level and
     `C_{Lj}(E) ≤ 2√(L_j(1−L_j))` (Prop. 2) at the channel level. **These two inequalities
     are the "how to bound an approximation's error vs an exact reference" the prompt asks
     for:** the worst-case coherence our incoherent leakage sim throws away is `≤ 2√(L_j(1−L_j))`,
     which is *small when the leakage rate is small* (`~2√L_j` for `L_j ≪ 1`) — exactly the
     transmon regime (`L_1 ~ 10^{-3}`–`10^{-5}`, Fig. 1). **Fig. 4 is the empirical version**
     of this bound: it shows precisely how far the depolarized approximation deviates from
     the exact coherent accumulation as a function of residual coherence `p`. We should
     report our leakage-teacher approximation error in **`C_L` / `C_{Lj}` units** and cite
     Props. 1–2 as the tightness certificate (saturated for pure states, so it is a real
     worst case, not loose).

3. **Lemma 2 (Eq. 69) licenses a Trotterized leakage teacher.** A circuit-level surface-code
   sim composes, per gate slice, an always-on dissipative `T1/T2`-leakage with a control
   unitary-leakage. Lemma 2 proves these **leakage/seepage rates add to second order in `Δt`**
   when the dissipators are ladder operators (which `D[a], D[a†]` are). So for a fine enough
   slice we may **sum** the thermal `L_1 ≈ κn̄Δt` and the control `L_1 ≈ ½sin²(Δt/2)` without a
   cross-term to leading order — the discretization that keeps a per-slice leakage teacher
   tractable and its error `O(Δt²)`-controlled. (This is the leakage analogue of standard
   Trotter error, here proved *for the leakage rates specifically*.)

4. **The decoder-input / soft-info connection.** The prompt asks for "the neural-decoder
   architecture + soft-info/leakage input." This paper does **not** build a decoder — it is
   a *characterization* paper. What it *does* give the decoder side: (i) the **leakage-induced
   phase error**, not the leakage rate, is the dominant logical effect (Fig. 1, Sec. III A,
   Sec. VI) — so a leakage-aware decoder's payoff is in catching that **coherent phase**
   signature, which on syndrome data shows as the **oscillation** fingerprint (Fig. 3 `p_{Π1}`,
   Fig. 4); (ii) a **measurement-leakage model** `Σ_j M_j = (1−q_1)Π_1 + q_2 Π_2` (Eq. A29)
   — the analogue of our soft-readout channel, with leakage during the 5 µs acquisition window
   (Sec. III A) as a concrete leakage-at-measurement mechanism to include. The *architecture*
   (GNN/Transformer with soft-info/leakage input) must come from the neural-decoder papers in
   the library (Bausch, scalable-neural-decoder, Pattison soft-information); this paper
   supplies the **physics of the input channel**, not the network.

5. **A clean, in-domain `do()`-knob and a calibration sanity check.** The `L_1:L_2` ratio is
   mechanism-diagnostic (erasure `L_2=0`; thermal `L_2≫L_1`; unital `d_1L_1=d_2L_2`) — a
   ready-made set of **controlled-teacher mechanisms** to `do()` between (e.g. "increase
   control-leakage `L_1` vs increase thermal seepage `L_2`," measure `ΔLER`). And the
   transmon LRB simulation (Sec. III A: `δ/2π=−300 MHz`, `κ=10 kHz`, `n̄=0.01`, 5 µs readout,
   8–30 ns pulses) is a **concrete, literature-anchored parameter set** for a realistic
   leakage teacher, with `(L_1, L_2, F)` values read directly off Figs. 1, 6.

## Limitations / what does NOT apply

- **W1 — it is a *characterization* framework, not a code/decoder simulation.** No surface
  code, no DEM, no logical error rate, no decoder appears. It defines and measures
  *single-gate* leakage `(L_1, L_2, F)` and their coherence; the *propagation* of leakage
  through QEC rounds, its effect on syndromes/`LER`, and any decoder must be supplied by us
  (and by the QEC-leakage papers: Suchara–Cross–Gambetta 1410.8562, Fowler 1308.6642,
  Miao 2211.04728, McEwen 2102.06131, the leakage-TN sim 2308.08186). This paper is the
  **model and metric layer**, not the **simulation-at-scale** layer.
- **W2 — the bounds are *bounds*, and the metrics are mostly incoherent.** `L_1, L_2, F` are
  blind to coherence by construction (Sec. IV opening); coherence is captured only by `C_L,
  C_{L1}, C_{L2}`, which **cannot be measured from `X_1` alone** (the whole point of Props.
  1–2 is to *bound* the unmeasurable coherence by the measurable rates). For our SIM teacher
  this is fine (we have the full qutrit state, so we can compute `C_L` exactly, not just
  bound it), but it means LRB-style *estimation* of our teacher's coherence is impossible —
  the coherence is a *simulator-internal* quantity, used to *score* the approximation, never
  recoverable from syndrome-only data. (Consistent with the project memo that coherence is
  not identifiable from syndrome-only data.)
- **W3 — Assumption 4 (full leakage-subspace depolarization) is exactly the regime where our
  *coherent* signal lives.** The clean single-exponential LRB model holds **only when the
  Clifford twirl also depolarizes `X_2`** (Eq. A16). When it doesn't (strong/coherent
  leakage), non-Markovian **oscillations** appear (Figs. 3, 4) and LRB *overestimates* the
  rates. So LRB is a poor estimator precisely in the coherent-leakage regime — again fine for
  us (we don't estimate; we simulate and score), but a warning that any "fit `L_1, L_2` from
  data" pipeline inherits this bias.
- **W4 — single-mode, weak-anharmonicity, single ladder structure.** The dissipative results
  (Lemma 2, thermal) assume **pure ladder operators** `A_{±k}` and a single anharmonic-oscillator
  mode; the additivity (Eq. 69) is **second-order in `Δt`** only. Strong leakage, non-ladder
  dissipators, or coarse time slices break the additivity and the closed forms. Multi-qubit
  leakage (Sec. V D) **ignores direct leakage-subspace interactions** (p. 14) — so genuine
  two-excitation / `|2⟩|2⟩` correlated leakage and leakage transport between neighbors (the
  surface-code-relevant correlated-leakage physics of McEwen/Miao) are **out of scope** here.
- **W5 — the worked numbers are single-qubit transmon-specific.** Figs. 1–6 (DRAG pulses,
  `δ/2π=−300 MHz`, `κ=10 kHz`, `n̄=0.01`) are calibration anchors, not surface-code data; the
  `1–2 orders` `L_1 < 1−F` gap and `L_2≫L_1` are transmon facts, not universal. Use them to
  *seed* the teacher's parameters, not as target `LER` numbers.

## How to use / trust + open questions
- **Trust:** high as the **canonical leakage-metric definition** (`L_1, L_2, C_L`, Props.
  1–2) and the **incoherent-approximation accumulation model** (Lemma 1) — these are the
  field-standard objects (cited as the metric source by AlphaQubit-class and Google leakage
  work). The additivity (Lemma 2) and closed-form thermal rates (Eqs. 78–79) are reliable
  to their stated second order. Carry W2/W3 (incoherent metrics; LRB bias under coherence)
  and W4 (single-mode, ladder, second-order) as scope.
- **Open questions for us:**
  (i) **Define our leakage-approximation error in `C_L`/`C_{Lj}` units** and certify it
  with Props. 1–2 (report worst-case coherence discarded `≤ 2√(L_j(1−L_j))`), with **Fig. 4**
  as the empirical comparison template — the concrete "bound vs exact qutrit reference"
  deliverable.
  (ii) **Adopt `(L_1, L_2)` as the leakage-teacher parameterization** (never `L_1+L_2`),
  seeded by the transmon numbers (Sec. III A, Figs. 1, 6), with one `|2⟩` level per data
  qubit (qutrit truncation, p. 13) as the minimal sim and Sec. V D for per-qubit rates.
  (iii) **Use Lemma 2 to justify a Trotterized `T1/T2`-leakage + control-leakage teacher**
  (additive rates per slice to `O(Δt²)`), and decide the slice `Δt` from the additivity
  error budget.
  (iv) **Pair this with a QEC-scale leakage propagation/decoder paper** (Suchara 1410.8562,
  Miao 2211.04728, leakage-TN 2308.08186, Pattison soft-info 2107.13589) for the parts this
  paper does not cover: leakage through rounds, syndrome signatures, and the neural decoder's
  soft-info/leakage input head.
