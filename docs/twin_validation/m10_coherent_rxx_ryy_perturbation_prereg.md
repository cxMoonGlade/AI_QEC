# M10 coherent_rxx_ryy_perturbation — Pre-Registration (theory-first, LITERATURE-GROUNDED, COMPOSITE)

Status: **PRE-REGISTRATION, 2026-06-30.** Predictions written BEFORE the run; a miss is a finding, not a
re-fit. The **COMPOSITE head** of the coherent 2q parasitic-coupling Hamiltonians group
(`axis1_mechanism_completeness_prereg.md` group 2: **M10 xx+yy**, M22 cxx, M23 cyy, M28 xy, M29 zx, M30 zy,
M31 xz, M32 yz, M33 yx). **Binding instruction (the brief): "XX+YY = fixed combo of M22+M23 — certify as
COMPOSITE, not an independent generator."** M10's reference operator is therefore the LITERAL SUM
`ref_H_M22 + ref_H_M23` of two already-(a)-class-grounded Cartan axes (the landed
`m22_coherent_cxx_parasitic_coupling_prereg.md` / `m23_coherent_cyy_parasitic_coupling_prereg.md`). Does NOT
claim Axis-1 completion and adds NO metric to `docs/METRICS.md` (`1−F_e` already in the ledger).

## 0. Grounding ledger (the corresponding papers — all 精读 + noted)

| sub-axis / item | paper(s) | support | reading note | in-repo code (reuse) |
|---|---|---|---|---|
| **OPERATOR** — the composite `X⊗X + Y⊗Y` as a standalone 2-body coherent generator (the *algebra*: a sum of two Cartan axes, written as a worked standalone gate) | Zhang–Vala–Sastry–Whaley arXiv:quant-ph/0209120 (Eq. 7 `p`=span of 9 Pauli⊗Pauli; Eq. 10 Cartan `a`={XX,YY,ZZ}; **Example 1(2) the "XY interaction" `¼(σ¹ₓσ²ₓ+σ¹ᵧσ²ᵧ)` = ¼(XX+YY) as an explicit standalone gate** generating the swap/Controlled-line) | **DIRECT** | `…/zhang_vala_sastry_whaley_weyl_chamber_quant-ph-0209120.md` (line 129/131: "XX+YY = the physical exchange combination = M22+M23 sum = fSim θ-swap") + `…/m10_xxyy_exchange_operator_grounding.md` | — |
| **OPERATOR** — `X⊗X + Y⊗Y` IS the fSim θ-swap block of a real Google two-qubit gate (device-physical) | Foxen et al. arXiv:2001.08343 (**Eq. 1** `fSim(θ,φ)`: θ-swap = `σXσX + σYσY`, φ=`σZσZ`; parasitic residual swap `δθ ≤ 5°`) | **DIRECT** | `…/foxen_fsim_twoqubit_gateset_2001.08343.md` (line 10, 28) + `…/m10_xxyy_exchange_operator_grounding.md` | — |
| **OPERATOR** — `(g12/2)(X⊗X + Y⊗Y)` = the MEASURED transverse exchange of a real transmon pair | Sung et al. arXiv:2011.01261 (`H_xx,direct = g12(σ⁺σ⁻+σ⁻σ⁺) = (g12/2)(XX+YY)`; **measured `g12/2π = 5.0 MHz`**, Table I; swap-rate spectroscopy) | **DIRECT** | `…/sung_zzfree_iswap_transverse_coupling_2011.01261.md` (line 44, 61-64, 92) + `…/m10_xxyy_exchange_operator_grounding.md` | — |
| **OPERATOR (INDIRECT)** — each summand as a canonical commuting generator; the sum as the `S_x+S_y` partial Cartan sum; the bounding device-physics (gmon always-on = pure-XX, exchange adds YY) + magnitude | Kraus–Cirac arXiv:quant-ph/0011050 (Eq. 12 `Σ_β α_β σ_β⊗σ_β`; Eq. 24/26 `S_x,S_y`); Geller arXiv:1405.1915 (always-on coupler = pure XX, no YY); Yan arXiv:1803.09813 / Mundada arXiv:1810.04182 (few-MHz transverse exchange) | **INDIRECT** | the four sibling notes (all 精读) | — |
| **OBSERVABLE** — process (entanglement) infidelity `1−F_e` of a CPTP map / unitary error | Schumacher PRA 54, 2614 (1996) (`F_e` def + Kraus form `Σ_k|Tr(ρE_k)|²`); Nielsen arXiv:quant-ph/0205035 (Eq. 3 `F_avg=(d F_e+1)/(d+1)`; **Eq. 16** `F_e=|Tr U/d|²` for unitary U) | **DIRECT** | `…/schumacher_nielsen_entanglement_fidelity_quant-ph-0205035.md` | `forward/joint_lindbladian.py:_choi_state_from_kraus`, `_state_fidelity`, `assemble_substep_channel` |
| M10 canonical definition | — | — | `docs/error_mechanisms.md` line 101 (M10 = `coherent_rxx_ryy_perturbation`, "composed RXX(eps_x) and RYY(eps_y) unitary", "parasitic XX/YY coupling") + `2q_parasitic_coupling_hamiltonians_theoretical_derivation.md` §M10 (`H_M10 = J_coh(X⊗X+Y⊗Y) = 2J_coh(σ⁺⊗σ⁻+σ⁻⊗σ⁺)`) | `mechanisms/catalog.py:MECHANISMS["M10"]` |

**Why the OPERATOR viewpoint clears the (a)-class threshold (≥2 DIRECT close-read) — and exceeds it.**
**THREE independent DIRECT close-reads** license the composite `X⊗X + Y⊗Y` as a standalone 2-body coherent
generator: (i) **Zhang** — Example 1(2) writes `¼(XX+YY)` (the "XY interaction") as an explicit standalone
gate generating the swap line, on the same footing as the pure-axis examples; XX and YY are the first two
Cartan axes (Eq. 10). (ii) **Foxen** — XX+YY IS the fSim θ-swap Hamiltonian block of a real Google
two-qubit gate (Eq. 1), with a device-measured *parasitic* residual swap `δθ ≤ 5°`. (iii) **Sung** —
`(g12/2)(XX+YY)` is the device transverse-exchange term, with the coefficient `g12/2π=5.0 MHz` MEASURED on
a real transmon pair. The two INDIRECT notes (Kraus–Cirac `S_x+S_y`; Geller/Yan/Mundada bounding) anchor
the magnitude `J_coh ≈ 2π×(0.01–3) MHz ≈ 10⁻⁴–10⁻² rad/ns` (parasitic floor) up to tens of MHz (gate-ON).
**Crucially: M10's grounding is STRONGER than its pure-axis summands** — the device-faithful object IS the
symmetric exchange XX+YY (Sung/Foxen write it out and measure it), whereas pure XX (M22) and pure YY (M23)
had to flag themselves as *idealized halves* of this exchange (M22 prereg S2 / M23 prereg S2; Sung note line
113-118; Zhang note line 131). The OBSERVABLE viewpoint clears threshold from the same DIRECT
Schumacher/Nielsen close-read the M6/M7/M20/M22/M23/M28 ledgers use (the `1−F_e=|Tr U/d|²` closed form is
generator-agnostic; only the trace value changes — for M10 the eigvals {−2,0,0,2}, §2 B1).
**operator_threshold_met = true (3 DIRECT); observable_threshold_met = true (1 DIRECT, exceeds the
1-DIRECT+3-INDIRECT floor via the M6/M7/M20/M22/M23/M28 precedent).** ⇒ epistemic_class='a',
implement-from-equations gate PASSES.

**Composite-symmetry note (why M10 is NOT new physics over M22+M23).** At the OPERATOR level M10 is the
exact sum of the two landed Cartan axes: `H_M10 = (coeff/4)(X⊗X+Y⊗Y) = H_M22 + H_M23`. The carrier already
lowers `COH_XX_YY` via the identical `_coherent_family_generator` path with `pairs=(("X","X"),("Y","Y"))`
(`axis1_mcwf_mps_execution.py` line 1092, the fall-through default). No NEW physics or new operator is
introduced; only the *sum* of two already-certified pairs. The ONE genuinely new content is the observable
(§2 B1: `1−cos⁴(ε/4)`, ratio 1/8 — distinct from the pure-axis `sin²(ε/4)`, ratio 1/16 — because XX+YY has
eigvals {−2,0,0,2}, not {±1}×2). Per the light-weight-path rule a single-builder + reviewer pass is
appropriate (the heavy ≥3-builder split is reserved for novel physics).

## 1. The mechanism (anchored; REUSE existing carrier code)

**M10 = coherent_rxx_ryy_perturbation = a 2q `exp(−i ε (XX+YY)/2)`-type coherent unitary error**
(`docs/error_mechanisms.md` line 101), the parasitic **transverse exchange / flip-flop / iSWAP** coupling
between two computational qubits. It is the **symmetric, excitation-preserving** combination of the pure-XX
(Cartan) and pure-YY (Cartan) axes (Zhang Eq. 10 + Ex. 1(2) `¼(XX+YY)`), physically the **fSim θ-swap block**
(Foxen Eq. 1) and the **device transverse exchange `(g12/2)(XX+YY)`** (Sung) — the coherent 2-body parasitic
term the twin's teacher composes with stochastic Pauli. `X⊗X + Y⊗Y = 2(σ⁺⊗σ⁻ + σ⁻⊗σ⁺)` preserves total
excitation number (the "XY interaction").

**Carrier form (the operator under test — REUSE, do not rebuild):** family `COH_XX_YY` (in
`TWO_SITE_COHERENT_FAMILIES`, `axis1_mcwf_mps_execution.py` line 80), lowered by
`_hamiltonian_matrix_for_term` (line 883; dispatch `if family in COHERENT_PAULI_FAMILIES`, line 934) →
`_embed_coherent_generator` (line 1104; level-selective embed of the 4×4 onto the computational levels
{0,1}×{0,1}, zero on leaked levels ≥2) → `_coherent_family_generator` (line 1011; the fall-through default
`pairs=(("X","X"),("Y","Y"))` for `COH_XX_YY`, line 1092, returning `(0.25·coeff)·(X⊗X + Y⊗Y)`). On the
**4-dim computational subspace**:

```
H_M10 = (coeff / 4) · (X ⊗ X + Y ⊗ Y) ,   X=[[0,1],[1,0]],  Y=[[0,-i],[i,0]]   # rad/ns; zero generator on any leaked level
        eigenvalues of (X⊗X + Y⊗Y) = {-2, 0, 0, +2}     # 2-dim kernel: |Φ⁺⟩=(|00⟩+|11⟩)/√2, |Ψ⁻⟩=(|01⟩-|10⟩)/√2
        (X⊗X + Y⊗Y) is NOT an involution:  (X⊗X+Y⊗Y)² = 2I + 2·(X⊗X)(Y⊗Y) ≠ I  (||(XX+YY)²−I||_F = 4.47)
        Tr(X⊗X + Y⊗Y) = 0 ,  X⊗X + Y⊗Y is REAL-SYMMETRIC (both summands are)
```

**M10-specific structural fact (the one place the composite differs from a single Pauli pair at the matrix
level):** unlike pure XX/YY (where `(P⊗P)²=I`, eigvals `{±1}×2`), the EXCHANGE `X⊗X+Y⊗Y` has eigvals
`{−2,0,0,+2}` with a **2-dimensional kernel** — so it is NOT an involution, and the realized gate is
`exp(−i(ε/4)(XX+YY))` with a NON-trivial spectral structure (identity on the kernel, ±(ε/2) phase on the
swap doublet). [Class (a) — an exact algebraic fact, derivation-checked: `(XX+YY)²−I` Fro-norm = 4.47,
eigvals = {−2,0,0,2}.] The realized error gate over a substep `dt` is

```
U_M10 = exp(−i · H_M10 · dt) = exp(−i (ε/4) (X⊗X + Y⊗Y)) ,    ε ≡ coeff · dt   (rad)
      acts as:  I on the {|Φ⁺⟩, |Ψ⁻⟩} kernel;  rotates {|Φ⁻⟩, |Ψ⁺⟩} by phases e^{∓iε/2}.
      Tr(U_M10) = 2 + 2cos(ε/2) = 4cos²(ε/4).
```

**Convention bridge (catalog ↔ carrier, declared so the factor is auditable).** `error_mechanisms.md`
writes M10 as composed `RXX(ε_x)` and `RYY(ε_y)` unitaries (catalog angles); the carrier's
`(coeff/4)(X⊗X+Y⊗Y)` gives `exp(−i(ε/4)(XX+YY))` with `ε=coeff·dt` — the **symmetric isotropic** case
`ε_x=ε_y=ε`. The factor `1/4 = (1/2)²` is the two-qubit over-rotation convention
`R_{PQ}(ε_cat)=exp(−i(ε_cat/2)(P⊗Q))` applied to the carrier's `ε`-per-tensor (carrier docstring line
1026-1029). The cert sweeps `ε=coeff·dt` (the carrier's native angle); all closed forms below are in `ε`.
[Class (c) — a convention statement.]

**Swept range (NOT a frozen constant):** `ε ∈ {3e-1, 1e-1, 3e-2, 1e-2, 3e-3, 1e-3}` rad. Physical anchor:
the transverse exchange floor is `g12/2 ≈ 2π×2.5 MHz` (Sung `g12/2π=5.0 MHz`); over a ~20 ns substep
`ε = J_coh·dt` lands in this band, and the activated/gate-ON exchange (fSim θ up to π/2, Foxen) reaches
`ε` up to ~0.3+. The *parasitic* residual swap is `δθ ≤ 5° ≈ 0.087 rad` (Foxen). The cert uses `coeff` and
`dt_ns` independently so `ε = coeff·dt` is swept by varying either.

### 1a. RESOLUTION of the COH_* placement ambiguity (ALREADY LANDED with M6 — inherited)

The brief's placement ambiguity was resolved by the M6 work and **M10 inherits the resolution**:
`mechanisms/axis1_primitives.py` lines 19-24 carry the NOTE that `COH_*`/`COHERENT_PAULI_FAMILIES` are
intentionally **NOT** declared there ("advertising it here was a declaration-without-lowering faithfulness
trap, M6 pre-registration §1a"), and that **the sole canonical lowering site for coherent-generator
families is `simulator/axis1_mcwf_mps_execution._hamiltonian_matrix_for_term`** (via
`_embed_coherent_generator`/`_coherent_family_generator`). **The M10 cert imports the operator under test
from `axis1_mcwf_mps_execution._hamiltonian_matrix_for_term` ONLY, never from the `axis1_primitives`
registry, and must NOT import `_coherent_family_generator` / `_embed_coherent_generator` /
`*_COHERENT_FAMILIES`** (the anti-circular namespace gate, enforced by L10) — the same surface the
M6/M7/M20/M22/M23/M28 ledgers and the qutrit-leakage de-circularized cert use. [Class (c) — a build/placement
decision, already executed; no physics claim.]

## 2. Predicted observable (class (b) bands; ANCHORED — `1−F_e`, the RIGHT one, not invented)

**Observable = process (entanglement) infidelity `1 − F_e`** between the substep channel WITH the M10 error
knob and the substep channel WITHOUT it (the ideal/no-error reference) — the standard
`axis1_mechanism_completeness_prereg.md` line-98 cert observable (`assemble_substep_channel` → Choi-state
`F_e`). Schumacher/Nielsen def (reading note, Eq. 16 `F_e=|Tr U/d|²` for a unitary error); for the
EXCHANGE XX+YY 2-site error vs identity, **with d=4** and eigvals {−2,0,0,2} (the M10-specific spectrum,
NOT the pure-axis {±1}):

- **(B1) EXACT closed form [b-band, derivable to a-exact] — DISTINCT from M22/M23:**
  `Tr(U_M10) = e^{iε/2} + 1 + 1 + e^{−iε/2} = 2 + 2cos(ε/2) = 4cos²(ε/4)`, so
  `F_e(U_M10, I) = |Tr(U_M10)/d|² = |4cos²(ε/4)/4|² = cos⁴(ε/4)` ⇒
  **`1 − F_e = 1 − cos⁴(ε/4) = sin²(ε/4)·(2 − sin²(ε/4))`**.
  **This is NOT `sin²(ε/4)`** (the pure-axis M22/M23 form): the composite XX+YY has eigvals {−2,0,0,2} with
  a 2-dim kernel, so the trace is `4cos²(ε/4)` (not `4cos(ε/4)`), giving `cos⁴` (not `cos²`). Predicted: the
  carrier-side `1−F_e` (via `_choi_state_from_kraus`+`_state_fidelity`) equals `1−cos⁴(ε/4)` to the
  Uhlmann-estimator floor (~4e-8), monotone increasing in `|ε|`, **even in ε**
  (`1−F_e(ε)=1−F_e(−ε)`: `F_e(U)=F_e(U†)`).
  *Derivation-check (RTX 5090, 2026-06-30, `outputs/m10_coherent_rxx_ryy_fe_derivation_check.py`): carrier
  `1−F_e` vs `1−cos⁴(ε/4)` agree to band_resid ≤ 5.0e-8 across ε∈{0.3…1e-3}; the three identities
  `1−cos⁴(ε/4)`, `sin²(ε/4)(2−sin²(ε/4))`, eig-form agree to ≤2.2e-16; even-in-ε exact.*
- **(B2) LEADING-ORDER scaling [b-band] — ratio 1/8, NOT 1/16:** `1 − F_e ≈ ‖G‖²_F/d` with
  `G=(ε/4)(X⊗X+Y⊗Y)`, `‖G‖²_F=Tr(G²)=(ε/4)²·Tr((X⊗X+Y⊗Y)²)=(ε/4)²·8=ε²/2`, `/d=/4 → ε²/8` (METRICS.md `/d`,
  **d=4** for the 2-site window; `Tr((XX+YY)²)=Tr(2I+2 XX·YY)=8`). Predicted **quadratic** law:
  `1−F_e ∝ ε²` at small ε; `(1−F_e)/ε² → 1/8` as `ε→0` (**TWICE M22/M23's 1/16**, because two Cartan axes
  contribute). The exact form deviates from `ε²/8` at `O(ε⁴)` (since
  `1−cos⁴(ε/4)=ε²/8 − 5ε⁴/768 + …`) — a registered higher-order finding, NOT a carrier bug.
  *Derivation-check: ratio (1−F_e)/ε² = 0.1249 at ε=0.1, →0.125; lead `ε²/8` tracks exact to lead/exact
  = 1.0005× at ε=0.1, 1.0000× at ε=0.03 (∝ε⁴ deviation).*
- **(B3) AVG-GATE link [b-band]:** `1 − F_avg = (d/(d+1))(1−F_e) = (4/5)(1−cos⁴(ε/4))` — reported as a
  companion ONLY if an RB-comparable number is wanted; `1−F_e` stays the headline (carry the convention +
  the d=4 with the number).

**Statistic flagged INSUFFICIENT (do NOT headline):** `1−F_e` (or `1−F_avg`) is a *scalar average* measure
— coherent and stochastic channels of equal infidelity are indistinguishable by it, AND (the M10 form of the
caveat) `1−F_e=1−cos⁴(ε/4)` is identical for ANY excitation-preserving 2-body generator with the same
{−2,0,0,2} spectrum and same ‖G‖ (e.g. a different exchange like XZ+ZX) — so the scalar `1−F_e` cannot tell
**which** exchange the coupling is, only its magnitude (reading-note Limitations; the surface-code analogue
is the Bravyi twirl-underestimate, `correcting_coherent_errors_surface_1710.02270.md`). It CAN tell M10 from
the pure axes M22/M23 by the ratio (1/8 vs 1/16) — but that is a registered consequence, not a separator the
cert relies on. The cert therefore ALSO gates the **direct operator/generator identity** (B4 below) — and
for M10 the operator gate is the SOLE witness that the carrier emits the *sum of exactly two pairs* (XX AND
YY), not a single pair (M22 alone / M23 alone) nor a wrong sign (XX−YY) nor a wrong pair (ZZ/XY).

- **(B4) OPERATOR identity [a-exact, the load-bearing gate] — the COMPOSITE identity:** the carrier
  generator equals the hand-typed **sum** reference: `‖H_carrier − H_ref‖_F ≤ 1e-12` and
  `‖U_carrier − U_ref‖_F ≤ 1e-10`, with `H_carrier` Hermitian (`‖H−H†‖_F ≤ 1e-12`) and traceless
  (`|Tr H| ≤ 1e-12`), where **`H_ref = (coeff/4)(X⊗X + Y⊗Y) = ref_H_M22 + ref_H_M23`** (the COMPOSITE — the
  literal sum of the two landed pure-axis references). A miss is a CARRIER PHYSICS BUG. **For M10 this gate
  is load-bearing in a way it is not for a scalar cert:** since `1−F_e` is exchange-blind (B1), B4 is the
  SOLE witness that the carrier couples via `XX+YY` (both pairs, plus sign) and not pure-XX / pure-YY /
  XX−YY / ZZ / XY. M10-sharp: `X⊗X+Y⊗Y` is real-symmetric, anti-diagonal `diag-anti = [0,2,2,0]` pattern
  (`(XX+YY) = [[0,0,0,0],[0,0,2,0],[0,2,0,0],[0,0,0,0]]`) — a pure-XX reference (`[[0,0,0,1],[0,0,1,0],
  [0,1,0,0],[1,0,0,0]]`), pure-YY, XX−YY (sign-flipped `[[0,0,0,−2]…]`), ZZ (diagonal), or XY (imaginary)
  is caught by B4 immediately (derivation-check: pure-XX/pure-YY diff 5.00e-2, XX−YY diff 1.00e-1, ZZ/XY
  diff 8.66e-2 at ε=0.1 — all ≫ 1e-3). **The COMPOSITE check `H_ref = ref_M22 + ref_M23` (to 0.0) IS the
  brief's "certify as composite, not an independent generator" instruction made executable.**

## 3. Independent ground truth (non-circular) — the HAND-TYPED reference operator (the COMPOSITE)

The reference is **hand-typed in the cert from the literature equations**, importing NO carrier symbol
(`_coherent_family_generator`, `_embed_coherent_generator`, `TWO_SITE_COHERENT_FAMILIES`,
`COHERENT_PAULI_FAMILIES` appear NOWHERE in the cert's executable code). The carrier side imports ONLY
`_hamiltonian_matrix_for_term` (the object under test) — exactly the de-circularized
`axis1_qutrit_leakage_certification` / M6 / M7 / M20 / M22 / M23 / M28 ledger pattern.

**Reference operator spec (PROVENANCE-carried, transcribed not invented; the COMPOSITE):**

```
# M10 reference generator on the 4-dim computational subspace ({0,1}x{0,1}), zero generator on leaked levels.
# H_M10 = (coeff/4) * (sigma_x (x) sigma_x  +  sigma_y (x) sigma_y)  ==  ref_H_M22 + ref_H_M23.  [COMPOSITE]
#   sigma_x = [[0,1],[1,0]],  sigma_y = [[0,-i],[i,0]]   <- Pauli (Nielsen & Chuang Eq. 2.1).
#   X(x)X + Y(x)Y is the EXCHANGE / flip-flop interaction 2(s+ (x) s- + s- (x) s+), the symmetric sum of the
#               first two Cartan axes of the non-local su(4) subalgebra a={XX,YY,ZZ}
#               (Zhang-Vala-Sastry-Whaley arXiv:quant-ph/0209120 Eq. 10), written as the standalone
#               "XY interaction" gate H = 1/4 (XX+YY)  (Zhang Example 1(2)).
#   DEVICE origin (DIRECT): the fSim theta-swap block  theta(sigma_x(x)sigma_x + sigma_y(x)sigma_y)
#               (Foxen arXiv:2001.08343 Eq. 1; parasitic residual swap delta_theta <= 5 deg), and the
#               measured transverse exchange  (g12/2)(XX+YY), g12/2pi = 5.0 MHz  (Sung arXiv:2011.01261).
#   factor 1/4 = (1/2)^2: two-qubit over-rotation convention R_{PQ}(eps_cat)=exp(-i(eps_cat/2)(P(x)Q)),
#               carrier eps = coeff*dt per tensor (error_mechanisms.md line 101; carrier docstring 1026-1029).
#   M10 structural fact: XX+YY is REAL-SYMMETRIC, eigvals {-2,0,0,+2} (2-dim kernel |Phi+>,|Psi->),
#               NOT an involution ((XX+YY)^2 = 2I + 2 XX.YY != I).
def ref_H_M10(coeff, dim_pair, device):       # dim_pair=(d0,d1), each 2 (or 3 if qutrit carrier)
    X = tensor([[0,1],[1,0]], complex128, device)
    Y = tensor([[0,-1j],[1j,0]], complex128, device)
    gen4 = 0.25 * coeff * (kron(X, X) + kron(Y, Y))   # 4x4 on the {0,1}x{0,1} block; real-symmetric
    out = zeros((d0*d1, d0*d1), complex128, device)
    embed gen4[qrow,qcol] -> out[row,col] for li,ri,lo,ro in {0,1}:    # zero on any level >= 2
        row=lo*d1+ro, col=li*d1+ri, qrow=lo*2+ro, qcol=li*2+ri
    return out
# error unitary:  U = matrix_exp(-1j * dt_ns * H),  eps = coeff*dt.
#   acts as I on {|Phi+>,|Psi->}; e^{-/+ i eps/2} on {|Phi->,|Psi+>}.  Tr(U) = 2 + 2cos(eps/2) = 4cos^2(eps/4).
# EXACT 1-F_e reference (unitary vs identity, d=4):  1 - |Tr(U)/4|^2  ==  1 - cos^4(eps/4)  ==  sin^2(eps/4)(2-sin^2(eps/4)).
# LEADING 1-F_e reference:  ||(eps/4)(XX+YY)||_F^2 / 4  ==  (eps/4)^2 * 8 / 4  ==  eps^2/8   (ratio 1/8, NOT 1/16).
```

This is a closed-form theorem (the `exp(−i(ε/4)(XX+YY))` matrix + `F_e=|Tr V/d|²` with the {−2,0,0,2}
spectrum), independent of the implementation. A from-scratch numerical confirmation on RTX 5090 already ran
(`outputs/m10_coherent_rxx_ryy_fe_derivation_check.py`, 2026-06-30): the carrier `COH_XX_YY` op equals
`(coeff/4)(X⊗X+Y⊗Y)` and equals `ref_H_M22+ref_H_M23` to **opdiff 0.0** across ε∈{0.3…1e-3} and
dim∈{(2,2),(3,3)}; eigvals = {−2,0,0,2}; `(XX+YY)²−I` Fro-norm = 4.47 (not an involution); `1−cos⁴(ε/4)`
vs the carrier Choi `1−F_e` agree to ≤5.0e-8 (Uhlmann floor); `ε²/8` tracks the exact form with the
predicted `O(ε⁴)` deviation; `H` Hermitian + traceless + real-symmetric residuals exactly 0; `1−F_e` even
in ε; the qutrit (3,3) embed has full opdiff 0, max leaked row/col norm 0. (That script is a
derivation-check, NOT the cert.)

**Wrong-component / wrong-axis negative controls (the controls a `1−F_e`-only / scalar cert structurally
CANNOT provide for M10) — the load-bearing M10 controls:** **WRONG-COMPONENT** references
`H_wrong ∈ {(coeff/4)(X⊗X) [=M22, one summand only], (coeff/4)(Y⊗Y) [=M23, one summand only],
(coeff/4)(X⊗X−Y⊗Y) [wrong sign — the anti-symmetric exchange], (coeff/4)(Z⊗Z), (coeff/4)(X⊗Y)}` must
DISAGREE with the carrier: `‖H_carrier − H_wrong‖_F ≥ 1e-3` (derivation-check at ε=0.1: pure-XX/pure-YY
each diff 5.00e-2, XX−YY diff 1.00e-1, ZZ/XY each diff 8.66e-2 — all ≫ 1e-3). **The pure-XX (=M22) and
pure-YY (=M23) "one-summand-only" controls are the load-bearing ones for M10:** because the carrier MUST
emit the *sum of both pairs*, a corruption that drops one summand (returns only XX, or only YY) is the most
likely M10-specific bug, and the COMPOSITE reference `ref_M22+ref_M23` is the SOLE thing that detects it.
The **XX−YY sign control** detects a relative-sign corruption (the anti-symmetric vs symmetric exchange).
A weaker `wrong_unit` control (treat `coeff` as the angle, dropping the ÷4 → `coeff·(XX+YY)`, or the 1-site
÷2 → `(coeff/2)(XX+YY)`) is retained as further controls (derivation-check: 2.12e-1, 7.07e-2). **Show the
controls trip:** corrupt the carrier pair list `COH_XX_YY→((X,X),(Y,Y))` to drop a pair (e.g. `((X,X),)`)
and confirm the hand-typed `(XX+YY)` composite reference CATCHES it (diff ≥ 1e-3, cert fails), while a
reference derived FROM the corrupted carrier list would mirror it to diff 0 (false-pass) — the C2-falsifier
shape of `test_wc_cert_catches_corrupted_carrier_level_map` / `test_m22_…_broken_wrong_axis_trips`.

## 4. Bounded simplifications (declared; unbounded ⇒ STOP)

- **S1 — XX+YY error treated as a STRICT unitary (pure Hamiltonian, no collapse).** Class (a) on the
  certified slice: M10 is by definition a coherent unitary (`docs/error_mechanisms.md` line 101); the cert
  certifies the Hamiltonian generator + the exact `exp(−iHdt)` gate. Error vs faithful: 0 (it IS the
  faithful object). ⇒ **STRICT gate tier** `1−F_e ≤ 1e-6` and operator identities `≤ 1e-12/1e-10` (no
  collapse ⇒ no finite-microstep MCWF error; the exact-dense regime, not the GROSS tier).
- **S2 — ISOTROPIC, equal-coefficient XX+YY (`ε_x=ε_y`) with NO induced ZZ (the device-faithfulness
  simplification — BOUNDED).** Class (b)/(c): the certified M10 is the SYMMETRIC exchange `(coeff/4)(XX+YY)`
  (equal weights). The device exchange `(g12/2)(XX+YY)` IS symmetric in RWA (Sung — the flip-flop block is
  intrinsically `XX+YY` with equal weight), so this matches the device-faithful object. **What is omitted:**
  (i) a co-occurring `J σz⊗σz` (the fSim φ-phase / residual ZZ, Foxen Eq. 1 / Sung ζ) — **error bound
  (transcribed):** Sung cancels ζ to ≈ 0 (ZZ-free), and the fSim CZ separates φ from θ; the omitted ZZ is
  the separate `COH_ZZ`/`COH_CROSSTALK_ZZ` (M11) axis composed alongside (the carrier separates them); for a
  *parasitic transverse* M10 the ZZ is ≲ 5–20% of J_coh (Geller `J_ZZ≈g²/η`, M22 prereg S2). (ii) An
  *anisotropic* `ε_x≠ε_y` exchange — the carrier's `COH_XX_YY` is the isotropic `ε_x=ε_y` head; a general
  anisotropic exchange is the pure-XX (M22) + pure-YY (M23) composed with independent coefficients (the
  carrier separates COH_XX, COH_YY, COH_XX_YY). This simplification is **declared + bounded**; it does NOT
  affect the cert (which tests the isotropic XX+YY the carrier emits, exactly), only the *physical
  interpretation*. [Sung "the exchange is symmetric XX+YY"; Foxen "θ-swap = XX+YY, φ = ZZ separate".]
- **S3 — 2-level computational subspace per site; zero generator on leaked levels.** Class (a): the M10
  exchange acts on the computational `{|0>,|1>}` block of each site; in a qutrit/ququart carrier the
  generator is the same 4×4 `(coeff/4)(XX+YY)` embedded with the zero generator on any level ≥2 (matches
  `_embed_coherent_generator`, confirmed by the derivation-check dim=(3,3) run: full opdiff 0, leaked
  row/col norm 0). Error vs faithful: 0 within the stated semantics. **M10-specific note:** `exp(−i(ε/4)
  (XX+YY))` leaves any leaked level UNCHANGED (`exp(0)=1` on level ≥2) — M10 imparts NO population/phase to
  leaked levels; any leaked-level exchange (e.g. the `|11⟩↔|02⟩` resonance that DOES occur in the physical
  fSim, Foxen "leakage to |02⟩ is the dominant error") is a DIFFERENT mechanism (leakage transport,
  M34/LEAK_*), not M10. Same "identity on leaked levels" simplification as M6/M7/M20/M22/M23 S2/S3.
- **S4 — `ε = coeff·dt` constant across the substep (no intra-substep drift).** Class (b): drift of the
  coupling strength ACROSS cycles is M13 = Axis-2 (frozen), not M10. Error bound: `O(Δε/ε)`; within one
  substep with a declared instantaneous `coeff`, exact. Cross-cycle drift is explicitly out of this slice.
- **S5 — `1−F_e` reported via the Uhlmann sqrt/eigh Choi estimator (≈4e-8 floor at d=4).** Class (c): the
  estimator floors at ~4e-8 (documented in `composed_vs_joint_infidelity`; confirmed by the derivation-check
  band_resid ~3-5e-8), so `1−F_e` is reported as the standard-metric companion at that resolution; the
  LOAD-BEARING zero-tolerance gate is the direct operator identity (B4) at 1e-12, not the `1−F_e` value.
  **Note:** at the smallest swept ε (e.g. ε=1e-3 → `1−cos⁴(ε/4)≈1.25e-7`) the true `1−F_e` is near the
  estimator floor (derivation-check: carrier 9.56e-8 vs closed 1.25e-7), so the B1 band there is dominated
  by estimator resolution — the operator gate (opdiff 0) carries the cert there, as for M22/M23.

## 5. Epistemic status (METRICS-ladder)

- **(a) exact:** the COMPOSITE operator identity B4 (`H_carrier = (coeff/4)(X⊗X+Y⊗Y) = ref_M22+ref_M23` =
  hand-typed ref, Hermitian, traceless, real-symmetric; `U` acting as I⊕rotation on the
  kernel/swap-doublet); the closed forms `1−F_e=1−cos⁴(ε/4)=sin²(ε/4)(2−sin²(ε/4))` and `‖G‖²_F/d=ε²/8`;
  the eigvals {−2,0,0,2} + non-involution `(XX+YY)²=2I+2XX·YY`; the wrong-component control disagreements;
  the even-in-ε symmetry; the zero-on-leaked-levels embed. These are theorems/identities — the only class
  anything is built on.
- **(b) bands:** B1 (carrier `1−F_e` = `1−cos⁴(ε/4)` to estimator floor; exchange-blind scalar), B2
  (quadratic `∝ε²`, ratio →1/8 — TWICE M22/M23), B3 (`1−F_avg=(4/5)·`), the `O(ε⁴)` exact-vs-leading
  deviation, and the S2 device-interpretation bound (isotropic XX+YY, omitted ZZ ≲5-20% / cancellable).
  A miss is a finding.
- **(c) gates:** STRICT numeric tiers (`1−F_e ≤ 1e-6`, operator `≤ 1e-12/1e-10`, wrong-component `≥ 1e-3`);
  the placement-fix decision (§1a, inherited); the catalog↔carrier convention bridge (§1); the swept ε grid.
- **Headline verdict stays PROVISIONAL** until the GPU cert runs green AND the corruption-falsifier (drop a
  pair) trips. Reportable + go/no-go; nothing is built on it. No Axis-1-completion claim, no METRICS change.

## 6. Build org + gate plan

- **Gate tier:** **STRICT** (`1−F_e ≤ 1e-6`; operator-identity `≤ 1e-12`/unitary `≤ 1e-10`) — M10 is a
  pure-Hamiltonian / exact-dense error (no collapse, no finite-step MCWF). NOT the GROSS+convergence tier
  (that is only for collapse-bearing first-order MCWF). Support size: **2 sites, d=4** (and a d=(3,3) embed
  check that the qutrit-carrier op is the computational-4-block + zero generator on leaked).
- **Independent-operator plan:** hand-typed `ref_H_M10 = (coeff/4)(XX+YY)` (§3) in the cert module, with an
  EXPLICIT `ref_H_M22 + ref_H_M23` composite-equality assertion (the brief's "certify as composite"
  instruction), importing only `_hamiltonian_matrix_for_term` from the carrier; `1−F_e` via
  `_choi_state_from_kraus`+`_state_fidelity`. Wrong-component (drop-XX / drop-YY / sign-flip XX−YY) +
  wrong-axis (ZZ / XY) + wrong-unit (÷4→×1, ÷4→÷2) negative controls — **the drop-summand controls are the
  load-bearing M10 ones** (a corruption that emits only one pair); a corruption falsifier (carrier pair list
  `COH_XX_YY→((X,X),(Y,Y))` corrupted to `((X,X),)` → hand-typed composite ref catches it; circular ref
  would false-pass). The cert mirrors `tests/test_m22_coherent_cxx_constraint_ledger.py` /
  `tests/test_m23_coherent_cyy_constraint_ledger.py` with: (i) the reference replaced by the SUM `(XX+YY)`
  on d=4 + a `ref_M22+ref_M23` equality test; (ii) the family string `COH_XX→COH_XX_YY`; (iii) the closed
  form `sin²(ε/4)→1−cos⁴(ε/4)`, ratio `1/16→1/8`, `F_avg` `(4/5)` unchanged; (iv) the wrong-component
  controls `{drop-XX, drop-YY, XX−YY, ZZ, XY}` (drop-summand is the new load-bearing one); (v) the
  non-involution / {−2,0,0,2}-eigval structural assertion; (vi) L9 the leaked-level embed over the
  4-computational-level layout. The L1-L10 invariant set carries over verbatim in structure from M22/M23.
- **GPU-only, serialized:** assert `torch.cuda.is_available()`; CUDA-missing fails the collection (memory
  rule). Scripted-execution; the cert lands commit-gated.
- **If built heavy:** M10 introduces NO novel physics beyond the landed M22/M23 machinery — it is the
  literal SUM of the two already-certified Cartan axes (the COMPOSITE), with one new observable
  (`1−cos⁴(ε/4)`, ratio 1/8). Per the light-weight-path rule a **single-builder + reviewer** pass is
  appropriate; the heavy ≥3-disjoint-builder split is reserved for novel physics, which M10 is not.
