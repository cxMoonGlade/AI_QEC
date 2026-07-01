# G2 — multi-qubit independent-boson closed-form oracle (derivation)

**Date 2026-07-01. Closes the one blocking theory gate (§G) of `coupling_simulator_n3n4_prereg.md` (v3).**
This is the PRIMARY Rule-I oracle for the coupling simulator: the exact reduced dynamics of a **multi-qubit
pure-dephasing Gaussian bath**, derived from the **bare system-bath Hamiltonian** via the Gaussian cumulant —
with **ZERO reference to the pseudomode construction (`K,g,Γ`)**, so it cannot share the carrier's blind spot
(anti-circular, Rule I). Epistemic class **(a) exact** (a theorem for a Gaussian bath; the 2nd cumulant is
exact for linear coupling to a Gaussian environment).

## 1. Model (the bare Hamiltonian — NOT the pseudomode)
`H = H_S + H_B + H_SB`, pure dephasing:
- `H_SB = Σ_{i=1}^n c_i Z_i B_i`, `Z_i` = Pauli-Z on qubit `i` (eigenvalues ±1), `c_i` real coupling, `B_i`
  Hermitian bath operators. `[H_S, Z_i]=0` (H_S diagonal in the computational basis, or 0) ⇒ **pure
  dephasing** (populations frozen, coherences decay).
- Bath Gaussian, stationary, `⟨B_i⟩_B=0`, factorized init `ρ(0)=ρ_S(0)⊗ρ_B`. The bath is FULLY characterized
  by the **matrix BCF** `C_{ij}(t)=⟨B_i(t)B_j(0)⟩_B`, `B_i(t)=e^{iH_B t}B_i e^{-iH_B t}`. Stationarity ⇒
  `C_{ji}(τ)=C_{ij}(−τ)*`.
- **Independence note:** `B_i`, `C_{ij}` are the ABSTRACT bath operators / correlation functions. The oracle
  never inverts or references the pseudomode `K=H−iΓ` or coupling `g`. (In the simulator, the designed
  shared-mode bath HAPPENS to realize a particular `C_{ij}`; the oracle takes `C_{ij}` as its only input and
  computes `ρ_S` by a DIFFERENT path — the cumulant — than the pseudomode's Lindblad evolution. Agreement
  certifies the Lindblad construction; sharing the input `C_{ij}` is the legitimate closed-form-vs-simulation
  check, not circularity.)

## 2. Derivation (interaction picture + Gaussian 2nd cumulant)
Interaction picture w.r.t. `H_0=H_S+H_B`. Since `[Z_i,H_S]=[Z_i,Z_j]=0`, the computational basis `{|a⟩}` is
preserved and `Z_i(s)=Z_i`. The coupling is `H_SB^I(s)=Σ_i c_i Z_i B_i(s)`. The propagator
`U_I(t)=T exp(−i∫₀ᵗ Σ_i c_i Z_i B_i(s)ds)` acts within each computational sector: with `Z_i|a⟩=z_i^a|a⟩`,
```
U_I(t)|a⟩ = |a⟩ ⊗ V_a(t),   V_a(t)=T exp(−i∫₀ᵗ Φ_a(s)ds),   Φ_a(s)=Σ_i w_i^a B_i(s),   w_i^a ≡ c_i z_i^a.
```
`w_i^a` = the effective coupling weight of qubit `i` in state `a`. The reduced coherence (interaction picture):
```
ρ_{ab}(t) = ρ_{ab}(0) · ⟨V_b†(t) V_a(t)⟩_B = ρ_{ab}(0) · ⟨ T̄ e^{i∫Φ_b} · T e^{−i∫Φ_a} ⟩_B.
```
Gaussian bath, `⟨Φ⟩=0` ⇒ the **2nd cumulant is EXACT**. This is the Feynman–Vernon influence phase for a
forward path with weights `w^a` and a backward path with weights `w^b`. Splitting the BCF into its real
(symmetric/noise) and imaginary (antisymmetric/dissipation) parts gives the standard result
```
ρ_{ab}(t) = ρ_{ab}(0) · exp(−Γ_{ab}(t)) · exp(−i φ_{ab}(t)),
```
with (the cross terms `w_i^a w_j^b − w_i^b w_j^a` in the phase cancel against the symmetry of `Im C_ij`):
```
Γ_{ab}(t) = Σ_{ij} (Δw)_i (Δw)_j Γ^R_{ij}(t),        (Δw)_i = w_i^a − w_i^b              [DECAY]
φ_{ab}(t) = Σ_{ij} (w_i^a w_j^a − w_i^b w_j^b) Γ^I_{ij}(t)                                 [LAMB PHASE]
Γ^R_{ij}(t) = ½ ∫₀ᵗ∫₀ᵗ Re C_{ij}(s₁−s₂) ds₁ds₂  =(diagonal/symmetric)= ∫₀ᵗ (t−τ) Re C_{ij}(τ) dτ
Γ^I_{ij}(t) = ½ ∫₀ᵗ∫₀ᵗ Im-part(antisym) …        =(diagonal)=            ∫₀ᵗ (t−τ) Im C_{ij}(τ) dτ
```
(The double-integral forms are unambiguous for off-diagonal `i≠j`; the `(t−τ)` single integral is the
diagonal/symmetric reduction used in the v1 pilot.)

## 3. THE ORACLE (full complex — finding B)
```
ρ_{ab}(t) = ρ_{ab}(0) · exp( −Σ_{ij} (Δw)_i (Δw)_j Γ^R_{ij}(t) ) · exp( −i Σ_{ij} (w_i^a w_j^a − w_i^b w_j^b) Γ^I_{ij}(t) )
```
`w_i^a = c_i z_i^a`, `z_i^a=±1`, `(Δw)_i = w_i^a − w_i^b`, `Γ^{R/I}_{ij}` from the matrix BCF `C_{ij}` DIRECTLY.
**Magnitude AND phase** — a magnitude-only form (`exp(−Σ(Δw)(Δw)Γ^R)`) is WRONG for sector-mixing coherences
(the v1 pilot's 0.34 disagreement); the Lamb phase `Γ^I` is required.

## 4. Reduction checks (all analytic; reproduce the v1 numerics)
1. **n=1 (single qubit, coupling c).** `|0⟩(z=+1)`–`|1⟩(z=−1)`: `Δw=2c`, `w^a=c,w^b=−c`. Decay `=(2c)²Γ^R_{11}
   =4c²Γ^R_{11}`; Phase `=(c²−c²)Γ^I_{11}=0`. An ISOLATED qubit has **no Lamb phase** (equal self-energies).
   [`c=½` ⇒ `exp(−Γ^R)` = v1 single-qubit; `c=1` ⇒ `exp(−4Γ^R)`.]
2. **n=2 rank-1 collective (v1: single shared mode, `C_{ij}=C ∀ij`, `c=½`).**
   - `|00⟩–|11⟩`: `Δw=(1,1)`. Decay `=(Σ_iΔw_i)²Γ^R=(2)²... =4Γ^R`? — `Σ_{ij}(Δw)_i(Δw)_jΓ^R=(1+1)²Γ^R=4Γ^R`.
     Phase `=(Σw_i^a)²−(Σw_i^b)² = 1−1 = 0`. ⇒ `exp(−4Γ^R)`, no phase. ✓ (v1 matched 2.5e-8).
   - `|01⟩–|10⟩` (DFS): `Δw=(1,−1)`. Decay `=(Σ_iΔw_i)²Γ^R=(0)²=0` → PROTECTED. ✓ (v1 = 0 exactly).
   - **1-qubit reduced** (Tr over q1) = `|00⟩–|10⟩` (phase `+Γ^I`) + `|01⟩–|11⟩` (phase `−Γ^I`), each decay
     `Γ^R` → `ρ^{(0)}_{01}=½e^{−Γ^R}(e^{−iΓ^I}+e^{+iΓ^I})=½e^{−Γ^R}cos Γ^I`. ✓✓ (v1 Lamb form, matched 2e-7).
3. **Diagonal / private bath (`C_{ij}=δ_{ij}C_{ii}`).** Decay `=Σ_i(Δw_i)²Γ^R_{ii}` (no cross terms). `|01⟩–|10⟩`:
   `Δw=(2c,−2c)` → decay `=4c²(Γ^R_{00}+Γ^R_{11}) ≠ 0` → **NOT protected**. ✓ (a DFS requires a SHARED bath;
   independent baths dephase the `|01⟩↔|10⟩` coherence). **This is the partial-correlation discriminator:** the
   `|01⟩⟨10|` DFS is fully protected ONLY for the rank-1 fully-correlated case; for partial correlation
   (`0<|C_{ij}|<√(C_{ii}C_{jj})`) it decays partially — the C4 falsifier of the prereg.
4. **Sign/factor convention.** `w_i^a=c_i z_i^a`, `z=±1`; `c=½` matches v1 (`S=Z/2`), `c=1` for `S=Z` (the
   n=3–4 rung). Decay is even in `Δw`; phase is the difference of branch self-energies (quadratic in each
   branch's weights) — vanishes for coherences with `Σw^a·w^a = Σw^b·w^b` (e.g. collective `|00⟩–|11⟩`).

## 5. How to operate / verify (independence-preserving)
- **Compute `Γ^{R/I}_{ij}(t)`** from the designed bath's `C_{ij}(t)` by quadrature (as v1 did for the diagonal),
  double-integral for off-diagonals. NEVER from the pseudomode `K`.
- **Numerical verification** (`outputs/g2_oracle_verify.py`): reuse the v1 GKSL engine (an INDEPENDENT
  computation — Lindblad evolution, not the cumulant) for the rank-1 single-mode case and compare the **full
  complex** `ρ_{ab}(t)` (magnitude AND phase) to this oracle. The multi-mode partial-correlation verification
  rides on the n=3–4 prototype (a designed shared-mode bath) once built.
- **Positive/negative controls:** motional-narrowing (non-oscillatory `C_{ij}`) ⇒ `Γ^R` monotone ⇒ no revival;
  a perturbed `C_{ij}` must break the oracle agreement (the v1 negative-control pattern).

## 6. Status
**G2 CLOSED (analytic + numeric).** The full-complex oracle is derived from the bare Hamiltonian, independent
of the pseudomode; all four reduction checks pass analytically and reproduce the v1 numerics. The FULL-COMPLEX
spot-check (`outputs/g2_oracle_verify.py`, 2026-07-01) confirms it against the INDEPENDENT v1 GKSL (Lindblad
evolution, not the cumulant): **max|ρ_GKSL − ρ_oracle| = 1.03e-7** over all coherences — including the
sector-mixing `|00⟩⟨10|` / `|01⟩⟨11|` (Lamb-phase `P=±1`, 1.03e-7), the collective `|00⟩⟨11|` (2.5e-8), and
the `|01⟩⟨10|` DFS (exactly 0). The Lamb-phase sign/convention is correct (no magnitude-only fallback needed).
Class **(a) exact** for the Gaussian pure-dephasing bath. **C3 of the prereg may now cite this oracle.**
