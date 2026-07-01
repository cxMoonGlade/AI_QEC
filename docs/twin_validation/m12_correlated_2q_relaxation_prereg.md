# M12 correlated_two_qubit_relaxation — Pre-Registration (theory-first, LITERATURE-GROUNDED)

Status: PRE-REGISTRATION, 2026-06-30. Predictions written BEFORE the build (the M12 carrier
seam does not yet exist). A miss is a finding, not a re-fit. Epistemic class: **(a)** for the
operator + observable (literature-grounded explicit Lindblad jump + Schumacher/Nielsen `1-F_e`);
**(c)** for the cooperativity magnitude `eta` (swept). The witness numbers in §2 were produced
by the from-scratch GPU derivation-check `outputs/m12_correlated_2q_relaxation_fe_derivation_check.py`
(RTX 5090, 2026-06-30) — a HAND-TYPED reference (raw Pauli, from-scratch dense Liouvillian, no
carrier operator builder), so the predictions are *anchored*, not invented.

> **Mechanism class:** M12 is a same-substep **two-site JOINT collapse operator** (the collective
> Dicke jump), Axis-1. The carrier's collapse path is currently **1-site only**
> (`axis1_mcwf_mps_execution.py::_collapse_operator`, applied on `where=support[0]`); M12 is the
> first mechanism that needs the **2-site joint-collapse seam** (item 4 of the
> `axis1_mechanism_completeness_prereg.md` missing list).

---

## 0. Grounding ledger (the corresponding papers — all 精读 + committed reading notes)

| viewpoint / sub-item | paper(s) | support | reading note | in-repo code (reuse) |
|---|---|---|---|---|
| **OPERATOR — DIRECT #1 (explicit collective Lindblad master eq., SC transmons)** — the dissipator with the cross-relaxation coefficient matrix `gamma^down_jk`; the off-diagonal `gamma_12 = g1 g2 (Gamma_b(w1)+Gamma_b(w2)^*)` is the correlated rate; the **symmetric limit `g1=g2, Δω=0` gives a single `gamma=gamma_jk`** ⇒ exactly `L = sqrt(gamma)(σ1^-+σ2^-)` | **Cattaneo–Giorgi–Maniscalco–Paraoanu–Zambrini arXiv:2005.06229** (PRA 103, 062217 (2021)): **Eq. (4)** dissipator `Σ_jk γ↓_jk(σ^-_j ρ σ^+_k − ½{ρ,σ^+_k σ^-_j}) + …`; **Eq. (A1)** `γ↓_jk = g_j g_k(Γ_β(ω_j)+Γ_β(ω_k)^*)+ (1/T1)δ_jk`; §V.A.2 (txt line ~592) "single dissipative coefficient `γ = γ↓_jk = γ↑_jk`", antisymmetric state in a decoherence-free subspace (`λ^(0)_5=0`, never decays) | **DIRECT** | `reading_notes/cattaneo_bath_induced_collective_superconducting_2005.06229.md` | — (new seam) |
| **OPERATOR — DIRECT #2 (canonical Lehmberg–Agarwal collective master eq.)** — the explicit two-emitter collective-decay master equation with collective damping `γ_ij`; **collective-state rates `γ+γ_12` (symmetric/superradiant), `γ−γ_12` (antisymmetric/subradiant)**; `γ_12 → γ` at small separation | **Z. Ficek arXiv:1002.4124** (review, 2010): **Eq. (47)** Lehmberg–Agarwal master eq. `dρ/dt = −iω0/2 Σ[S^z_i,ρ] − i Σ_{i≠j}Ω_ij[S^+_iS^-_j,ρ] − ½ Σ_{ij}γ_ij({ρS^+_i,S^-_j}+{S^+_i,S^-_jρ})`, `γ_ii≡γ` (Einstein A); **Eq. (48)** collective damping `γ_ij`; **Eq. (53)** rate eqs `ρ̇_ss=−(γ+γ_12)(ρ_ss−ρ_44)`, `ρ̇_aa=−(γ−γ_12)(ρ_aa−ρ_44)`; **Eq. (50)** `γ_12→γ` as `kr_12→0` | **DIRECT** | `reading_notes/ficek_multiatom_entanglement_lehmberg_agarwal_1002.4124.md` | — (new seam) |
| **OPERATOR — DIRECT (method) / INDIRECT (operator) — the MCWF collective-jump diagonalization** — the recipe to put the cross-damped dissipator on a quantum-jump (MCWF) carrier: diagonalize the Hermitian `γ` matrix → collective jumps `C_s = sqrt(Γ_s)U^-_s`, `C_a = sqrt(Γ_a)U^-_a` | **C. A. McDermott arXiv:2201.11193** (2022): **Eq. (41)** cross-damped two-atom relaxation superoperator; **Eq. (43)** `U^±_s=(S^±_1+S^±_2)/√2`, `U^±_a=(S^±_1−S^±_2)/√2`; **Eq. (45–46)** `C_s=sqrt(Γ_s)U^-_s`, `Γ_s=½(Γ+Γ_12)`, `C_a=sqrt(Γ_a)U^-_a`, `Γ_a=½(Γ−Γ_12)` | **DIRECT (MCWF method) / INDIRECT (operator)** | `reading_notes/mcdermott_quantum_jump_two_atoms_2201.11193.md` | `axis1_mcwf_mps_execution.py::_sample_joint_jump_or_nojump` (the MCWF unraveling to extend) |
| **OPERATOR — INDIRECT (SC-qubit rate structure)** — two SUPERCONDUCTING qubits, common bath, `Γ_s=2Γ_0`, `Γ_a=0` (the defining collective signature); does NOT write the explicit Lindblad jump operator | **Ojanen–Niskanen–Nakamura–Abdumalikov arXiv:0705.1085** (2007): Eq. 3 single-qubit rate; `Γ_{φs}=2Γ_{2→1}`, `Γ_{φa}=0` (J=0, equal couplings); Eq. 5 subradiant `∝(g1−g2)^2` | **INDIRECT** | `reading_notes/ojanen_global_relaxation_superconducting_0705.1085.md` | — |
| **OPERATOR — INDIRECT (SC-qubit measured magnitude / cooperativity bound)** — two transmons sharing a cavity: **measured `Γ_bright=2Γ_κ`, `Γ_dark=0` ⇒ cooperativity `η=Γ_12/γ≈1` (2× enhancement)**; bounds `γ_corr ≤ γ_1` | **Mlynek–Abdumalikov–Eichler–Wallraff arXiv:1412.2392** (Nat. Commun. 5, 5186 (2014)): Fig. 4 `Γ_bright=2Γ_κ`, `Γ_dark=0`; `Γ_κ/2π≈0.48–0.54 MHz` | **INDIRECT** | `reading_notes/mlynek_dicke_superradiance_two_qubits_1412.2392.md` | — |
| **OPERATOR — INDIRECT (non-additivity of a collective L)** — `L=A+B` cannot be split into two independent Lindblad operators without dropping the cross terms (the mathematical reason the joint collapse ≠ two independent T1) | **Jaschke–Montangero arXiv:1804.09796**: App. A, "a Lindblad operator `L=A+B` cannot be split into two independent Lindblad operators `A` and `B`" | **INDIRECT** | `reading_notes/jaschke_open_quantum_tensor_networks_1804.09796.md` | — |
| **OBSERVABLE — DIRECT** — process (entanglement) infidelity `1−F_e` of a CPTP map, computed as the Uhlmann fidelity of the trace-normalized Choi states | **Schumacher PRA 54, 2614 (1996)** (`F_e` def + Kraus form `Σ_k|Tr(ρE_k)|²`); **Nielsen arXiv:quant-ph/0205035** (Eq. 3 `F_avg=(d F_e+1)/(d+1)`; Choi-state form) | **DIRECT** | `reading_notes/schumacher_nielsen_entanglement_fidelity_quant-ph-0205035.md` | `forward/joint_lindbladian.py::_choi_state_from_kraus`, `_state_fidelity`, `assemble_substep_channel` |

**Threshold verdict (LITERATURE-SUPPORT GATE, (a)-class) — applied to BOTH viewpoints:**
- **OPERATOR:** **2 DIRECT close-read** (Cattaneo Eq.4/A1 — explicit Lindblad dissipator + cross-rate, ON SC TRANSMONS; Ficek Eq.47/53 — canonical Lehmberg–Agarwal collective master eq. + super/sub-radiant rates) **+ 4 INDIRECT close-read** (McDermott MCWF diagonalization [also DIRECT-method]; Ojanen SC rate structure; Mlynek SC measured 2×; jaschke non-additivity). This **closes the gap the Ojanen+Mlynek notes flagged** ("certificate-grade for the operator form requires a standard reference that explicitly derives the Lindblad Dicke master equation" — Cattaneo + Ficek ARE that reference). **operator_threshold_met = true (2 DIRECT, ≥ the ≥2-DIRECT branch).**
- **OBSERVABLE (`1−F_e`):** **1 DIRECT** (Schumacher/Nielsen — the same close-read every Axis-1 mechanism-completeness cert uses; the Choi-state form transfers verbatim to a collapse channel). The M6/M7/M10/M20/M22/M23/M28 precedent. **observable_threshold_met = true.**
- ⇒ **epistemic_class = 'a', implement-from-equations gate PASSES.**

---

## 1. The mechanism (anchored; the swept range, never a frozen constant)

**M12 = correlated two-qubit relaxation** — the same-substep collective Dicke jump on a qubit
pair `(i,j)`:
```
L_M12 = sqrt(gamma_corr) (σ^-_i ⊗ I_j + I_i ⊗ σ^-_j) = sqrt(gamma_corr)(σ^-_i + σ^-_j)
```
- `σ^- = |0><1| = [[0,1],[0,0]]` (Nielsen & Chuang; the amplitude-damping lowering operator).
- Grounded by Cattaneo Eq.(4)+(A1) (SC transmons, explicit dissipator + cross-rate) and Ficek
  Eq.(47)+(53) (canonical Lehmberg–Agarwal collective master eq.).
- **MCWF-ready (diagonalized) form** (McDermott Eq.43–46), the form the carrier seam builds:
  ```
  C_s = sqrt(Gamma_s) (σ^-_i + σ^-_j)/sqrt(2),   Gamma_s = gamma + gamma_12   [symmetric/superradiant]
  C_a = sqrt(Gamma_a) (σ^-_i − σ^-_j)/sqrt(2),   Gamma_a = gamma − gamma_12   [antisymmetric/subradiant]
  ```
  where `gamma ≡` single-qubit T1 rate, `gamma_12 ≡ eta·gamma` the correlated cross-rate.

**Swept parameter — `eta = gamma_12 / gamma ∈ [0, 1]` (the cooperativity fraction), class (c):**
- `eta = 0` → independent baths: `Gamma_a = Gamma_s = gamma`, M12 reduces to two independent
  M4/M24 (T1) channels (no collective effect).
- `eta = 1` → fully cooperative common bath (the physical maximum): `Gamma_s = 2γ`, `Gamma_a = 0`
  (antisymmetric DARK). Only the symmetric collective jump `sqrt(γ)(σ^-_i+σ^-_j)` survives —
  exactly `L_M12`. This is the Mlynek (measured 2×) / Ojanen / Cattaneo symmetric-limit maximum.
- `0 < eta < 1` → partial cooperativity: BOTH `C_s` and `C_a` survive.
- **No read paper measures the incidental `eta` for a real multi-qubit superconducting QEC
  processor** (Mlynek/Cattaneo are engineered common baths; Ficek's `γ_12(kr_12)` is free-space
  geometry). SWEEP `eta`; physical bound `eta ≤ 1`. Declared **class (c) heuristic gate** — a
  swept design constant, NOT a prediction band, NOT a premise.
- `gamma` (single-qubit baseline) swept over `1/(10–100 μs)` (current transmons); the substep
  exposes `kappa = gamma·dt` (the dimensionless decay weight per substep).

---

## 2. Predicted observables (class (b) bands; ANCHORED — witnessed by the from-scratch check)

The observable is the **process infidelity `1−F_e`** of the M12 substep channel (Schumacher/Nielsen;
Uhlmann fidelity of trace-normalized Choi states), `d = 4` (two-site computational space).

**B1 — entangled-jump action (a)-class exact (structural, not a band).** `L_M12|11> = |01>+|10>`
(the |01>,|10> superposition); the **antisymmetric state `|Ψ_a> = (|01>−|10>)/√2` is DARK**
(`L_M12|Ψ_a> = 0`). WITNESS (derivation-check): resid `0.00e+00` for both. This is the collective
Dicke signature distinguishing M12 from independent T1, grounded by Ficek Eq.53 (`γ−γ_12→0`).

**B2 — `1−F_e` is LINEAR in `κ = γ·dt` at leading order (collapse channel).** Predicted:
`1−F_e ≈ κ + O(κ^2)` (the collective channel from `|11>/|10>/|01>`-supported amplitude damping),
i.e. `(1−F_e)/κ → 1` as `κ → 0`. **Contrast the coherent over-rotation mechanisms (M6/M10/M22…)
which are QUADRATIC in `ε`** — this is the qualitative collapse-vs-coherent separator. WITNESS:
```
κ        1−F_e        (1−F_e)/κ
0.30     2.4239e-01   0.808
0.10     9.2899e-02   0.929
0.01     9.9254e-03   0.993        → ratio → 1.0 (LINEAR), confirmed.
```
Falsifiable bet: `(1−F_e)/κ → 1` (linear), NOT `→ const·κ` (quadratic). [class (b)]

**B3 — MCWF first-order convergence (GROSS tier + `O(1/m^2)`).** The collapse-bearing gate is
**GROSS `1−F_e ≤ 1e-1`** at `microstep_count = 1` (the ~1e-2 finite-step error is CORRECT), with
`O(1/m^2)`-ish convergence as `m` grows. WITNESS (`κ=0.1`, MCWF first-order channel vs exact expm):
```
m     1−F_e(MCWF_m vs exact)   ratio_to_prev
1     4.9549e-03               —          (≤ 1e-1 GROSS ✓)
2     3.9209e-04               12.6
4     7.9532e-05               4.93
8     1.8205e-05               4.37
32    1.0367e-06               4.19       → ~4× per doubling = O(1/m^2), confirmed.
```
Falsifiable bet: doubling `m` shrinks the MCWF-vs-exact `1−F_e` by ≈4× (the leading correction is
`O(1/m^2)`). [class (b)/(c) — the gate tier]

**B4 — joint collective ≠ two independent T1 (the physical content).** The fully-cooperative M12
channel (`gamma_12 = gamma`) is DISTINGUISHABLE from two independent T1 channels (`gamma_12 = 0`):
WITNESS:
```
κ        1−F_e(joint vs independent)
0.30     1.3021e-01
0.10     5.2628e-02
0.03     1.7004e-02      → large, joint != independent, confirmed.
```
This is the M12 raison d'être, grounded by the off-diagonal `gamma_12` (Cattaneo Eq.A1) and the
non-additivity `L=A+B` (jaschke). [class (b)]

**INSUFFICIENT statistic (do NOT use as the headline):** a *single-qubit marginal* T1 decay curve
of either qubit CANNOT distinguish M12 from independent T1 — the collective effect is in the
*joint* (two-qubit) dynamics / the dark subradiant mode. The headline is the joint-channel `1−F_e`
and the dark-state annihilation (B1/B4), not a per-qubit relaxation rate. (Cf. Ojanen: the
super/subradiant split is a *collective-state* phenomenon; Cattaneo: subradiance needs the
two-qubit negativity, not a local observable.)

---

## 3. Independent ground truth (non-circular)

**The reference operator is HAND-TYPED from raw 2×2 Pauli matrices** (`σ^- = [[0,1],[0,0]]`),
built into the collective jump `L = sqrt(γ)(σ^-⊗I + I⊗σ^-)` and the diagonalized `C_s, C_a`
(McDermott Eq.43–46) — **importing NOTHING from the carrier's operator builders**
(`_collapse_operator` / `_hamiltonian_matrix_for_term`). Provenance: arXiv ids + exact equation
numbers transcribed in the reading notes (Cattaneo Eq.4/A1; Ficek Eq.47/53; McDermott Eq.43–46).

**The reference CHANNEL is a from-scratch dense Liouvillian** (`L = Σ_k conj(C)⊗C −
½ I⊗C^†C − ½ (C^†C)^T⊗I`, column-stacking) → `expm` → Choi-eigendecompose → Kraus —
**NOT `assemble_substep_channel`** (the anti-toy protocol: `assemble_substep_channel` shares the
carrier's term-builder seam, so it certifies grouping/propagation ONLY; a wrong sign/operator
would pass it). The from-scratch Liouvillian + hand-typed operator is operator-independent ground
truth. (`outputs/m12_correlated_2q_relaxation_fe_derivation_check.py`.)

**The `1−F_e` observable** is the Schumacher/Nielsen Choi-state fidelity (`_choi_state_from_kraus`
+ `_state_fidelity`) — the same machinery every Axis-1 cert uses; it is the OBSERVABLE definition,
not a carrier operator, so reusing it is not circular (the operator under test is hand-typed).

**The cert plan (when the carrier seam is built):**
1. Build the carrier's M12 substep channel via the new 2-site joint-collapse path (the diagonalized
   `C_s, C_a` on `where=(i,j)`).
2. Build the reference channel from the HAND-TYPED `L`/`C_s,C_a` via the from-scratch dense
   Liouvillian (independent of the carrier).
3. Compare `1−F_e(carrier, reference)`: **GROSS `≤ 1e-1`** at `microstep_count=1` + `O(1/m^2)`
   convergence (B3). The **exact-commuting structural control** (e.g. `gamma_12=0`, where the two
   collapse channels commute and the joint = composed) gates at **zero-tolerance** `≤ 1e-12`.
4. Controls (B1, B4, §6 wrong-operator) must trip as witnessed.

---

## 4. Bounded simplifications (declared; unbounded ⇒ STOP)

| # | simplification | epistemic class | error bound (vs faithful) |
|---|---|---|---|
| S1 | **Rotating-wave + Born–Markov** (the collective Lindblad form holds) | (a) under RWA/Born-Markov | RWA `O((g/Δ)^2) < 1e-4` (GHz qubits, MHz coupling); Born-Markov `O((γτ_B)^2) < 1e-6` (μs T1, ns bath). Both grounded: Cattaneo §(weak-coupling `ω≫μ/ℏ`, Ohmic ⇒ Markov), Ficek (Eq.47 at T=0 Born-Markov). |
| S2 | **First-order MCWF microstep at `m=1`** (collapse-bearing) | (c) gate tier | GROSS `1−F_e ≤ 1e-1`; the `~5e-3` (κ=0.1) finite-step error is CORRECT and shrinks `O(1/m^2)` (B3 witness). Bounded + convergent. |
| S3 | **Pairwise-only correlation** (no ≥3-qubit collective jumps) | (c) gate/decision | Triple correlations need three qubits sharing one mode (exponentially suppressed in a typical layout); the support is the qubit PAIR. The cert is on the 2-site window; higher-order is out of scope (bounded by exclusion). |
| S4 | **Fully-symmetric (`g1=g2, Δω=0`) cooperative limit as the headline** (`gamma_12=gamma`) | (c) swept | The general `0≤eta≤1` is representable (both `C_s,C_a` built); the symmetric limit is the maximal-effect headline (Cattaneo §V.A.2 single-`γ`; Mlynek measured 2×). `eta` swept, bound `eta≤1`. NOT a frozen "1–10%". |

No unbounded simplification. (The prior "1–10% × γ_1" magnitude was DELETED in the derivation doc —
fabricated DiVincenzo–Yang citation; replaced by the bracketed `eta∈[0,1]`, bound `eta≤1`.)

---

## 5. Epistemic status (METRICS-ladder)

- **(a) exact:** the operator `L = sqrt(γ_corr)(σ^-_i+σ^-_j)` (Cattaneo Eq.4 symmetric limit / Ficek
  Eq.47/53 / McDermott Eq.46); the entangled-jump action B1 (`L|11>=|01>+|10>`, dark `|Ψ_a>`,
  zero-tolerance structural identities); the `1−F_e` definition (Schumacher/Nielsen). These are the
  only items anything may be built on.
- **(b) bands (a miss is a finding):** B2 (`1−F_e` linear-in-κ, ratio→1), B3 (`O(1/m^2)` MCWF
  convergence), B4 (joint ≠ independent magnitude). Registered falsifiable bets, witnessed by the
  from-scratch check above.
- **(c) gates / swept:** `eta = gamma_12/gamma ∈ [0,1]` (the cooperativity; no sourced incidental
  hardware value; bound `eta≤1`); the GROSS `1−F_e ≤ 1e-1` gate tier at `m=1`; the zero-tolerance
  structural control (`gamma_12=0` commuting case); the wrong-operator controls (§6).
- **Headline verdict stays PROVISIONAL** until the carrier seam is built + certified vs the
  independent (hand-typed, from-scratch-Liouvillian) ground truth with convergence — reportable +
  go/no-go, nothing built on it.

---

## 6. Build org + wrong-operator controls

**Build (the carrier seam — the only new code):** extend `axis1_mcwf_mps_execution.py`'s collapse
path so a **2-site joint-collapse term** (`kind="collapse"`, `operator_family="CORR_RELAX"`,
`support=(i,j)`, params `gamma`, `eta`) builds the **diagonalized collective jumps** `C_s, C_a`
(McDermott Eq.43–46) as 4×4 operators on the joint support and samples among `{NO_JUMP, C_s, C_a}`
(the existing `_sample_joint_jump_or_nojump` logic, but the jump operator acts jointly on
`where=(i,j)`, not single-site `where=support[0]`). Owns the collapse path ONLY; the oracle
`assemble_substep_channel` (dense `c_list`) is unchanged. GPU-only; scripted-execution; the seam
change is commit-gated. Heavy enough for ≥3 disjoint builders + an un-led reviewer IF the MPS 2-site
gate plumbing turns out non-trivial; otherwise a single executor + a verifier pass.

**Wrong-operator controls (must trip, `||L_M12 − L_wrong||_F ≥ 1e-3`; WITNESSED):**
```
single-site s1 only        diff=1.4142   OK   (the 1-site collapse the old path would build — must differ)
single-site s2 only        diff=1.4142   OK
wrong sign (s1−s2)         diff=2.8284   OK   (the antisymmetric/dark jump, not the symmetric collective)
raising (σ^+ collective)   diff=2.8284   OK   (excitation, not relaxation)
```
These are the round-1 W-C circularity guard (a wrong sign/operator must NOT pass): the single-site
controls specifically catch the "declaration-without-2-site-lowering" trap — building M12 with the
old 1-site path would produce `single-site s1 only`, which the control rejects.

---

## 7. References (arXiv ids)

- **arXiv:2005.06229** — Cattaneo et al., bath-induced collective phenomena on SC qubits (PRA 103, 062217). OPERATOR DIRECT.
- **arXiv:1002.4124** — Ficek, multi-atom entanglement review; Lehmberg–Agarwal collective master eq. OPERATOR DIRECT.
- **arXiv:2201.11193** — McDermott, quantum-jump method for two atoms; MCWF collective-jump diagonalization. OPERATOR INDIRECT / METHOD DIRECT.
- **arXiv:0705.1085** — Ojanen et al., global relaxation in SC qubits (rate structure). OPERATOR INDIRECT.
- **arXiv:1412.2392** — Mlynek et al., Dicke superradiance for two transmons (measured 2×). OPERATOR INDIRECT (magnitude bound).
- **arXiv:1804.09796** — Jaschke & Montangero, open-quantum tensor networks (non-additivity of L=A+B). OPERATOR INDIRECT.
- **arXiv:quant-ph/0205035** + Schumacher PRA 54, 2614 (1996) — entanglement fidelity `1−F_e`. OBSERVABLE DIRECT.
