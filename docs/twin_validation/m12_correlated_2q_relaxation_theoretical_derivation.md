# M12 Correlated Two-Qubit Relaxation — Theoretical Derivation

Date: 2026-06-29 (citations re-grounded 2026-06-30). Status: **operator algebra (a)-class exact** (collective Dicke jump, RWA/Born-Markov); **magnitude (c)/bracketed** (cooperativity η ∈ [0,1], no sourced hardware value). Citations verified — one fabricated reference (DiVincenzo & Yang) deleted; see verdict table at end.

## Physical Origin

**M12 = correlated two-qubit relaxation** — the same-substep joint collapse operator that simultaneously relaxes two qubits. Physical origins in superconducting qubits include:

1. **Shared substrate phonon bath** — both qubits couple to the same lattice modes
2. **Flux-line crosstalk** — common flux bias line coupling to both qubits
3. **Capacitive crosstalk through a shared bus** — indirect coupling to a common electromagnetic environment
4. **Common readout resonator** — both qubits couple to the same measurement resonator

The key distinction from independent T1 (M4/M24) is that the **jumps are correlated**: when one qubit relaxes, the other has an enhanced probability of relaxing simultaneously.

---

## Mathematical Form (a-class — exact derivation)

### Standard Collective Damping (Dicke Model)

For two qubits coupled to a **common bosonic bath** in the **Born-Markov and rotating-wave approximations**, the reduced dynamics follow a Lindblad master equation with **collective (Dicke) jump operators** [Gorini, Kossakowski & Sudarshan, *J. Math. Phys.* **17**, 821 (1976) — the GKSL generator; Haroche & Raimond, *Exploring the Quantum*, OUP 2006, §collective damping — the Dicke collective-damping master equation; grounded for superconducting qubits by Ojanen et al., arXiv:0705.1085 and confirmed experimentally by Mlynek et al., Nat. Commun. **5**, 5186 (2014)]:

> **Citation correction (2026-06-30).** An earlier draft anchored this equation to "DiVincenzo & Yang, PR 1998, *Fluctuation-Dissipation Theorem and Qubit Spectral Function*". **That citation is FABRICATED** — no such paper exists (verified by WebSearch + arXiv; there is no DiVincenzo–Yang paper on this topic in any year/journal; the real DiVincenzo 1998-era work is Loss & DiVincenzo, PRA 57, 120, on quantum-dot spin qubits, unrelated). It has been deleted. The collective Dicke operator form is instead grounded in the references above (see verdict table + the two committed reading notes). The GKS journal was also wrong ("Rep. Math. Phys." → correct is *J. Math. Phys.* **17**, 821).

```
dρ/dt = -i[H, ρ] + Σ_{μ=±} D[L_μ](ρ)
```

where the **symmetric collective collapse operators** are:

```
L_+ = √γ_corr (σ₁⁺ + σ₂⁺)    // collective excitation
L_- = √γ_corr (σ₁⁻ + σ₂⁻)    // collective relaxation (our M12)
```

Here:
- `σ_j⁻ = |0⟩⟨1|_j` is the lowering operator for qubit j (amplitude damping)
- `σ_j⁺ = |1⟩⟨0|_j` is the raising operator (excitation)
- `γ_corr` is the **correlated relaxation rate** (ns⁻¹)
- `D[c](ρ) = c ρ c^† - ½{c^† c, ρ}` is the Lindblad dissipator

### The Joint Collapse Operator for M12

For **correlated relaxation only** (not excitation), the M12 mechanism corresponds to:

```
L_M12 = √γ_corr (σ₁⁻ ⊗ I_2 + I_1 ⊗ σ₂⁻) = √γ_corr (σ₁⁻ + σ₂⁻)
```

This operator acts on the **two-qubit Hilbert space** `(C²)⊗(C²)`. Its action on the basis states:

| Initial State | After Jump (probability ∝ γ_corr) |
|---------------|-----------------------------------|
| |11⟩ | (σ₁⁻ + σ₂⁻)|11⟩ = |01⟩ + |10⟩ (entangled output!) |
| |10⟩ | (σ₁⁻ + σ₂⁻)|10⟩ = |00⟩ |
| |01⟩ | (σ₁⁻ + σ₂⁻)|01⟩ = |00⟩ |
| |00⟩ | (σ₁⁻ + σ₂⁻)|00⟩ = 0 (no state) |

**Key feature:** Starting from |11⟩, the jump produces a **maximally entangled state** `(|01⟩ + |10⟩)/√2`. This is the physical signature of correlated relaxation.

### Distinguishability from Independent T1

Independent relaxation (two separate M4 channels) would have:

```
L_1 = √γ₁ (σ₁⁻ ⊗ I_2)
L_2 = √γ₂ (I_1 ⊗ σ₂⁻)
```

From |11⟩, this produces either |01⟩ or |10⟩, not the entangled superposition. The **joint operator L_M12** is fundamentally different.

---

## Physical Scaling and Magnitude

### Bath Correlation Function

The correlated rate `γ_corr` depends on the **overlap integral** of the two qubits' coupling to the shared bath modes:

```
γ_corr = ∫ dk J(k) g₁(k) g₂(k)  ×  δ(ω₁ - ω₂) [energy-conserving]
```

where:
- `J(k)` is the bath spectral density
- `g_j(k)` is qubit j's coupling to mode k
- The δ-function enforces energy conservation (near-degenerate qubits have the strongest correlation)

### Order-of-Magnitude Estimates — UNSOURCED → BRACKETED (epistemic class (c))

> **Magnitude correction (2026-06-30).** The earlier "γ_corr ≈ 0.01–0.1 × γ₁ (1–10%) [DiVincenzo 1998]"
> is **deleted**: the citation is fabricated AND the 1–10% number has **no source**. Worse, it is the
> wrong *direction* — the actual collective-relaxation physics for superconducting qubits bounds the
> correlated rate at **0 ≤ γ_corr ≤ γ₁**, with the maximum (γ_corr = γ₁, i.e. Γ_bright = 2γ₁,
> Γ_dark = 0) realized in the **fully cooperative** common-bath limit, NOT a 1–10% fraction. Anchors:
> Ojanen et al. (arXiv:0705.1085, theory: Γ_s = 2Γ₀, Γ_a = 0 for matched superconducting qubits) and
> Mlynek et al. (Nat. Commun. **5**, 5186 (2014), experiment: **measured 2× enhancement, η = Γ₁₂/γ₁ ≈ 1.0**).

Parameterize the correlated rate as `γ_corr = η · γ₁` with the **dimensionless cooperativity fraction
η ∈ [0, 1]**, then:

- Independent T1 baseline (illustrative, swept): `γ₁ ≈ γ₂ ≈ 1/(10–100 μs)` for current transmons.
- **`η` (cooperativity) — BRACKETED, no empirical anchor for the realized hardware value:**
  - `η = 0` → independent baths (M12 reduces to two independent M4/M24 channels).
  - `η = 1` → fully cooperative common bath = the **physical upper bound**; Γ_bright = 2γ₁, Γ_dark = 0.
    This is the *engineered-cavity* maximum (Mlynek), achievable by design, not an incidental noise level.
  - **Incidental / parasitic shared bath (the regime M12 actually targets — substrate phonons, stray
    modes, a shared bus):** η is an **open parameter**, `0 < η ≪ 1` plausible by order-of-magnitude, but
    **NO read paper measures the incidental fraction in a multi-qubit superconducting processor.** Declared
    epistemic class **(c) heuristic gate** (a swept design constant, NOT a prediction band, NOT a premise).
    SWEEP η; do not freeze a "1–10%" value as if sourced.

The correlation is strongest when (Ojanen §regime; Mlynek conditions for full cooperativity):
1. Qubits are **frequency-matched** (`ω₁ ≈ ω₂`) — energy-conserving collective decay.
2. Qubits have **matched bath couplings** (`g₁ ≈ g₂`); the subradiant/dark rate ∝ `(g₁−g₂)²` (Ojanen Eq. 5).
3. Qubits are **spatially close** / the shared coupling path is **direct** (long-wavelength common mode, `λ_env ≫ d₁₂`; or a common bus/resonator).

---

## Implementation in Axis-1 Carrier

### Operator Construction

> **Placement (2026-06-30, per the Axis-1 seam map):** M12's 2-site joint collapse is a NEW seam in
> **`src/qec_twin/simulator/axis1_mcwf_mps_execution.py`** (the collapse path —
> `_collapse_operator`/`_sample_joint_jump_or_nojump`, currently **1-site only**), NOT in
> `mechanisms/axis1_primitives.py`. The carrier seam builds the **diagonalized** collective jumps
> `C_s, C_a` (McDermott Eq. 46) so the MCWF unraveling has a diagonal Lindblad form; the dense
> `assemble_substep_channel` oracle takes the bare `c_list` (equivalent).

The collective jump operator on the joint 2-site (4×4) space:

```python
# Two-qubit Pauli matrices
sx_a = torch.kron(sx, eye)  # but we need sm = (sx - i*sy)/2
sm_a = torch.kron(sm, eye)  # σ₁⁻ ⊗ I
sm_b = torch.kron(eye, sm)  # I ⊗ σ₂⁻

# M12 joint collapse operator
coeff = math.sqrt(gamma_corr_per_ns)  # rate in ns⁻¹
L_M12 = coeff * (sm_a + sm_b)  # (4, 4) matrix on two-qubit space

# Add to c_list for joint propagation
c_list.append(L_M12)
```

### Support Specification

- **Support:** The qubit pair (i, j) that share the correlated relaxation
- **Parameter:** `gamma_corr_per_ns = η · γ₁` (ns⁻¹), with `η ∈ [0, 1]` the cooperativity fraction —
  **SWEEP `η`** (epistemic class (c) heuristic gate; no sourced hardware value; see magnitude section).
  Physical bound `η ≤ 1` (Mlynek 2× enhancement); do not hardcode a "0.001–0.01" value as if grounded.
- **Generator kind:** `collapse` (dissipative, same-substep)
- **Axis:** Axis-1 (instantaneous same-substep joint Lindbladian)

---

## Observable Signatures

### 1. Joint Decay Probability

The probability of **simultaneous two-qubit decay** in time dt is:

```
P(both) = γ_corr dt + O(dt²)
```

This is **higher than the independent prediction** `P(both)_ind = γ₁γ₂ (dt)²` for small dt.

### 2. Entangled Jump Products

A jump from |11⟩ produces `(|01⟩ + |10⟩)/√2`, which is entangled. This leaves **detectable phase correlations** in subsequent evolution.

### 3. Detector Correlation Structure

In a QEC circuit, correlated relaxation produces **spatial detector correlations** at the adjacent measure qubits that share the pair. The correlation persists for the relaxation lifetime.

---

## Bounded Simplifications (following FAITHFULNESS_PROTOCOL.md)

### Simplification 1: Rotating-Wave Approximation (RWA)
- **Epistemic class:** (a) — exact under RWA
- **Assumption:** The bath is weakly coupled, and counter-rotating terms `σ⁺ + σ⁺` are negligible
- **Error bound:** `O((g/Δ)²)` where g is coupling and Δ is bath detuning; for GHz-frequency superconducting qubits and MHz coupling, `error < 10⁻⁴`

### Simplification 2: Born-Markov Approximation
- **Epistemic class:** (a) — exact under Born-Markov
- **Assumption:** Bath correlation time `τ_B` is much shorter than system timescale `1/γ`
- **Error bound:** `O(γτ_B)²`; for transmons at 10-100 μs T1 and phonon bath `τ_B ~ 1 ns`, `error < 10⁻⁶`

### Simplification 3: Two-Qubit Window (Finite Support)
- **Epistemic class:** (c) — gate/decision rule
- **Assumption:** Correlated relaxation is **pairwise only** (no higher-order triple correlations)
- **Justification:** Hardware layouts typically couple qubits in pairs; triple correlations would require three qubits sharing the same mode, which is exponentially suppressed

---

## Independent Oracle for Certification

> **Anti-toy correction (2026-06-30).** `assemble_substep_channel` is NOT operator-independent —
> for the dense-Liouvillian it consumes the same `c_list` the carrier builds, so it certifies the
> GROUPING/PROPAGATION (the joint-vs-composed cross-terms), NOT the operator itself. A wrong
> sign/Pauli/coefficient in the M12 collapse would pass an `assemble_substep_channel`-vs-itself
> check. Per `docs/FAITHFULNESS_PROTOCOL.md`, the load-bearing certification is against an
> **operator-INDEPENDENT** ground truth: the **HAND-TYPED reference operator** `L = √γ(σ⁻⊗I +
> I⊗σ⁻)` built from raw 2×2 Pauli (`σ⁻=[[0,1],[0,0]]`), fed through a **from-scratch dense
> Liouvillian** `L = Σ_k conj(C)⊗C − ½ I⊗C^†C − ½ (C^†C)^T⊗I` → `expm` → Choi → Kraus, importing
> nothing from the carrier's `_collapse_operator`/`_hamiltonian_matrix_for_term`. This is
> `outputs/m12_correlated_2q_relaxation_fe_derivation_check.py` (GPU, RTX 5090, 2026-06-30).

To certify the carrier seam (once built):

1. Build the carrier's M12 substep channel via the new 2-site joint-collapse path (diagonalized
   `C_s, C_a` on `where=(i,j)`).
2. Build the **independent** reference channel from the HAND-TYPED operator + from-scratch dense
   Liouvillian (above) — operator-independent ground truth.
3. Compute process infidelity `1 − F_e(carrier, reference)` (Schumacher/Nielsen Choi-state form):
   **GROSS `≤ 1e-1`** at `microstep_count=1` + `O(1/m^2)` convergence (collapse-bearing tier).
4. **Distinguishability (the physical content):** `1 − F_e(E_joint[γ_12=γ], E_ind[γ_12=0])` is
   LARGE (≈0.13 at κ=0.3, witnessed) — the joint collective channel ≠ two independent T1 channels.
5. **Structural control (zero-tolerance):** for `γ_12 = 0` the two collapse channels commute, so
   `joint = composed` to `≤ 1e-12`; for `γ_corr = 0` M12 reduces to identity (no jump).

`assemble_substep_channel` remains a USEFUL *secondary* check (it confirms the carrier's
diagonalized-jump trajectory channel reproduces the dense Liouvillian's grouping), but it is NOT
the load-bearing operator certification.

---

## Next Steps

1. ~~**Literature close-read:** confirm the `L = √γ(σ₁⁻ + σ₂⁻)` form for superconducting qubits~~ **DONE** (2026-06-30): Ojanen + Mlynek 精读'd (rate structure). **Operator-form gap CLOSED (2026-06-30):** Ojanen/Mlynek give the *rate structure* but NOT the explicit Lindblad jump operator — the two DIRECT explicit-Lindblad anchors are now **Cattaneo arXiv:2005.06229** (Eq. 4 dissipator + Eq. A1 cross-rate matrix, ON SC TRANSMONS; symmetric limit single `γ`) and **Ficek arXiv:1002.4124** (Eq. 47 Lehmberg–Agarwal collective master eq. + Eq. 53 super/sub-radiant rates `γ±γ_12`), with **McDermott arXiv:2201.11193** (Eq. 43–46) the MCWF collective-jump diagonalization recipe. All three 精读'd, notes committed.
2. ~~**Write reading notes**~~ **DONE** (see References + the three new notes above).
3. ~~**Write pre-registration**~~ **DONE** (2026-06-30): `docs/twin_validation/m12_correlated_2q_relaxation_prereg.md` — operator (a)/explicit-Lindblad grounded; cooperativity η (c)/swept; predictions witnessed by `outputs/m12_correlated_2q_relaxation_fe_derivation_check.py` (GPU, RTX 5090). operator_threshold_met + observable_threshold_met = true; implement-from-equations gate PASSES.
4. **Implement the carrier seam:** extend `axis1_mcwf_mps_execution.py`'s COLLAPSE path (NOT `axis1_primitives.py`) to a **2-site joint collapse** — `CORR_RELAX` term builds the diagonalized collective jumps `C_s, C_a` (McDermott Eq. 46) on `where=(i,j)` and samples among `{NO_JUMP, C_s, C_a}` (the current `_collapse_operator`/`_sample_joint_jump_or_nojump` path is 1-site only). η swept. **(As built — matched-coupling limit (5-model review #7):** the seam implements the single collective operator `C_s = √γ(σ₁⁻+σ₂⁻)`; at matched coupling `γ₁₂=γ` the antisymmetric arm `C_a = √(γ−γ₁₂)(σ₁⁻−σ₂⁻) ≡ 0`, so the competition reduces exactly to `{NO_JUMP, C_s}`. The `C_a` arm — the `γ₁₂<γ` partial-cooperativity generalization — is a second `CORR_RELAX`-class collapse term, declared and deferred, not yet emitted.)
5. **Certify vs INDEPENDENT ground truth:** against the HAND-TYPED reference operator (raw Pauli) + a from-scratch dense Liouvillian (NOT `assemble_substep_channel` alone — it shares the carrier seam, certifies grouping/propagation only). GROSS `1−F_e ≤ 1e-1` at `microstep_count=1` + `O(1/m^2)` convergence; zero-tolerance for the `gamma_12=0` commuting structural control.

---

## References (verified 2026-06-30)

### Citation verdict table

| Citation as written (earlier draft) | Exists? | Supports the claim? | Real source / action |
|---|---|---|---|
| "DiVincenzo & Yang, PR 1998 / PRL 1998, *Fluctuation-Dissipation Theorem and Qubit Spectral Function*" (cited 3× — master eq. + magnitude anchor for γ_corr ≈ 0.01–0.1·γ₁) | **NO — FABRICATED.** WebSearch + arXiv find no DiVincenzo–Yang paper on this (any year/journal). Closest real work: Loss & DiVincenzo, PRA 57, 120 (1998) — quantum-dot spin qubits, unrelated to FDT/correlated relaxation. | **NO** (does not exist; the magnitude it "anchored" is therefore unsourced). | **DELETE** all 3 occurrences. The γ_corr ≈ 0.01–0.1·γ₁ magnitude is **unsourced → bracketed** (η ∈ [0,1], class (c)). |
| "Gorini et al., **Rep. Math. Phys.** 1976" (GKSL generator) | **Yes**, but **wrong journal.** Real: Gorini, Kossakowski, Sudarshan, *Completely positive dynamical semigroups of N-level systems*, **J. Math. Phys. 17, 821 (1976)**. | **Yes** (the GKSL generator is correctly the master-equation form). | **KEEP, journal corrected** to *J. Math. Phys.* **17**, 821. |
| "Haroche & Raimond, *Exploring the Quantum*, OUP 2006 (chapter on collective damping)" | **Yes** (real textbook; genuinely has the Dicke collective-damping / superradiance chapter). | **Yes** (standard reference for the collective-damping master equation + explicit Lindblad jump form). | **KEEP** (the textbook anchor for the explicit collective-Lindblad form Ojanen does not write out). |

### Verified, 精读'd anchors

**Operator form (collective Dicke jump `L = √γ_corr (σ₁⁻ + σ₂⁻)`):**
- **Gorini, Kossakowski, Sudarshan, *Completely positive dynamical semigroups of N-level systems*, J. Math. Phys. 17, 821 (1976)** — the GKSL generator (master-equation form).
- **Haroche & Raimond, *Exploring the Quantum: Atoms, Cavities, and Photons*, OUP 2006** — the explicit Dicke collective-damping master equation + jump operators (textbook standard; cf. Agarwal 1974, Lehmberg 1970). The explicit Lindblad jump-operator statement that Ojanen does not write out.
- **Ojanen, Niskanen, Nakamura, Abdumalikov Jr., *Global relaxation in superconducting qubits*, arXiv:0705.1085 (2007)** — derives, for two SUPERCONDUCTING (flux) qubits under a global common bath, the super/subradiant rate structure `Γ_s = 2Γ₀`, `Γ_a = 0` (the defining signature of the collective jump). Grounds the rate structure for SC qubits; does NOT itself write the Lindblad jump operator. → `ojanen_global_relaxation_superconducting_0705.1085.md`.

**Magnitude / cooperativity (experimental):**
- **Mlynek, Abdumalikov Jr, Eichler, Wallraff, *Observation of Dicke Superradiance for Two Artificial Atoms in a Cavity with High Decay Rate*, Nat. Commun. 5, 5186 (2014); arXiv:1412.2392** — measures, for two superconducting transmons sharing a cavity, **Γ_bright = 2Γ_single, Γ_dark = 0**, i.e. cooperativity **η = Γ₁₂/γ₁ ≈ 1.0 (2× enhancement, fully cooperative)**. This is the *engineered-cavity maximum*; it bounds γ_corr ≤ γ₁ and **refutes** the deleted "0.01–0.1·γ₁" both as direction and magnitude. → `mlynek_dicke_superradiance_two_qubits_1412.2392.md`.

**Magnitude verdict:** γ_corr has **NO sourced hardware value** for the *incidental/parasitic* shared-bath regime M12 targets. Physical bound `0 ≤ γ_corr ≤ γ₁` (η ∈ [0,1]); fully-cooperative max η=1 (Mlynek), independent baths η=0. The realized incidental fraction is **bracketed/swept (class (c) heuristic gate)** — no read paper measures it in a multi-qubit superconducting processor.

**Provenance:** The collective Dicke operator algebra (L_± = √γ_corr(σ₁∓ + σ₂∓); the |11⟩→(|01⟩+|10⟩)/√2 entangled-jump table) follows standard quantum-optics collective-damping theory + the GKSL formalism and is **(a)-class exact** under RWA/Born-Markov — UNCHANGED by this citation forensics. Only the citations/anchors were corrected: the fabricated DiVincenzo–Yang reference deleted, the GKS journal fixed, the magnitude re-grounded as a bracketed cooperativity fraction.