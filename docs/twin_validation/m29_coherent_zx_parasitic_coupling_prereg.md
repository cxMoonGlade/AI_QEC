# M29 coherent_zx_parasitic_coupling — Pre-Registration (theory-first, LITERATURE-GROUNDED)

Status: **PRE-REGISTRATION, 2026-06-29.** Predictions written BEFORE the run; a miss is a finding,
not a re-fit. Member of the **coherent 2q parasitic-coupling Hamiltonians** group
(`axis1_mechanism_completeness_prereg.md` group 2: M10 xx+yy, M22 cxx, M23 cyy, M28 xy, **M29 zx**,
M30 zy, M31 xz, M32 yz, M33 yx). **Direct sibling-in-machinery of the landed M22/M23**
(`m22_coherent_cxx_parasitic_coupling_prereg.md`, `m23_coherent_cyy_parasitic_coupling_prereg.md`) —
IDENTICAL cert pattern, a 2-SITE generator on d=4, factor 1/4 not 1/2, **the ZX (cross-resonance)
axis instead of XX/YY**. The load-bearing wrong-axis control is **ZX-vs-{XX,YY,ZZ,XZ,ZY,XX+YY}**, with
**XZ(=M31) the strictly-necessary swap-partner separator** (ZX≠XZ; M29 is asymmetric under qubit swap).
Does NOT claim Axis-1 completion and adds NO metric to `docs/METRICS.md` (`1−F_e` already in the ledger).

**M29 is the BEST-GROUNDED of the parasitic-coupling family** — unlike pure XX/YY (idealized canonical
Cartan axes that the device-physics notes flag as NOT the always-on parasitic), the **ZX interaction IS
the dominant physical two-qubit term in fixed-frequency-transmon devices**: it is the *cross-resonance
(CR) entangler itself* (Magesan–Gambetta arXiv:1804.04073 Eq. 3.16, `H_CR = … − (JΩ/√(Δ²+Ω²)) ZX/2`),
and *parasitic / residual ZX* (the un-echoed CR component, classical-crosstalk-induced ZX) is a named,
calibrated error source on IBM-architecture hardware. M29 is uniquely backed by **two independent
DIRECT-physical references — both device-real ZX**: Magesan 1804.04073 is the CR effective-Hamiltonian
*theory*; **Sheldon–Magesan–Chow–Gambetta arXiv:1603.04821 / PRA 93, 060302(R)** is the device
*measurement* — the IBM Hamiltonian-tomography experiment that measures `ZX = (Ω⁰_x − Ω¹_x)/2` (and the
six CR terms `{IX,IY,IZ,ZX,ZY,ZZ}`) directly on real fixed-frequency transmons. So for M29 the OPERATOR
grounding is *device-direct* (theory **and** measurement), not just algebra-direct.

## 0. Grounding ledger (the corresponding papers — all 精读 + noted)

| sub-axis / item | paper(s) | support | reading note | in-repo code (reuse) |
|---|---|---|---|---|
| **OPERATOR (device THEORY)** — `Z⊗X` as the **device-physical cross-resonance entangler**, written as an explicit Pauli⊗Pauli coefficient (the strongest, device-direct license) | Magesan–Gambetta arXiv:1804.04073 (**Eq. 3.16** ideal-qubit CR `H_CR = (Δ−√(Δ²+Ω²))·ZI/2 − (JΩ/√(Δ²+Ω²))·ZX/2`; **Eq. 3.14** `tr(H_CR·ZX/2)=−JΩ/√(Δ²+Ω²)` the ZX coefficient; Eq. 4.25/4.26 the realistic-transmon ZX `ZX/2|linear = −(JΩ/Δ)(δ₁/(δ₁+Δ))`; Appendix C the full {IX,IZ,ZI,ZX,ZZ} tensor with the **control-side restricted to {I,Z}** ⇒ ZX is the unique entangling 2-body term) | **DIRECT** | `…/magesan_gambetta_cross_resonance_pauli_tensor_1804.04073.md` (lines 54-81: "the interaction term that entangles is ZX") | — |
| **OPERATOR (device MEASUREMENT)** — `Z⊗X` **measured on real fixed-frequency transmons** via Hamiltonian tomography (the second device-direct license, complementary to Magesan's theory) | Sheldon–Magesan–Chow–Gambetta arXiv:1603.04821 / PRA 93, 060302(R) (**Eq. 2** the measured CR Hamiltonian structure `H = Z⊗A/2 + I⊗B/2`; **`ZX = (Ω⁰_x − Ω¹_x)/2`** extracted from the control-conditioned target x-Rabi rates; the six measured terms `{IX,IY,IZ,ZX,ZY,ZZ}`; "accurately measures the full CR Hamiltonian"; `J/2π=3.8 MHz`, `ZX` few-MHz; `ZX90` = CNOT generator; IRB `f=0.991±0.002` with cancellation vs `0.948±0.018` without) | **DIRECT** | `…/sheldon_cross_resonance_hamiltonian_tomography_1603.04821.md` ("the device MEASUREMENT of ZX, complementary to Magesan's effective-Hamiltonian theory") | — |
| **OPERATOR** — `Z⊗X = σ¹_z σ²_x` as a canonical, independent 2-body generator of the **non-local part `p` of su(4)** + the general anisotropic interaction with independent cross-coefficients | Zhang–Vala–Sastry–Whaley arXiv:quant-ph/0209120 (**Eq. 7** `p = span(i/2){…, σ¹_z σ²_x, σ¹_z σ²_y, σ¹_z σ²_z}` — **`σ¹_z⊗σ²_x` listed verbatim** as the 7th basis element; **Sec. V Ex. 2** `H = ½(J_xx XX + J_yy YY + J_xy XY + J_yx YX)` an explicit `Σ_ab J_ab σ_a⊗σ_b` with **independent** J_ab including the cross-terms ⇒ pure single cross-axis ZX is the one-coordinate point) | **DIRECT** | `…/zhang_vala_sastry_whaley_weyl_chamber_quant-ph-0209120.md` (lines 36, 69-72: ZX is a basis element of `p`; Ex.2 gives `Σ J_ab σ_a⊗σ_b` with independent cross-coefficients) | — |
| **OPERATOR (bounding/INDIRECT)** — where ZX does/does not come from device-physically: the **always-on transverse coupler is XX (NOT ZX)** (so ZX is the *driven/CR* axis, distinct from the gmon term), and the device exchange is XX+YY; magnitude anchors | Geller-Martinis arXiv:1405.1915 (Eq. 57 `δH=g σx⊗σx`; the always-on transverse term is XX, **no driven ZX in the bare coupler**); Mundada arXiv:1810.04182 (exchange `J(σ⁺σ⁻+σ⁻σ⁺)`, residual `ζ/2π=2.26 MHz`, "few-MHz" band; the always-on parasitic is **ZZ**, transverse is exchange); Kraus-Cirac arXiv:quant-ph/0011050 (Eq. 12 `U_d=e^{−iσ_A^T d σ_B}`, **d diagonal** ⇒ only XX/YY/ZZ — so a pure cross-term ZX is an *off-diagonal* anisotropic axis, requiring local dressing to reach the Cartan frame; the [α_x,α_y,α_z] precursor) | **INDIRECT** | `…/geller_gmon_tunable_coupler_xx_zz_1405.1915.md`, `…/mundada_qubit_crosstalk_exchange_coupling_1810.04182.md`, `…/kraus_cirac_two_qubit_canonical_quant-ph-0011050.md` | — |
| **OBSERVABLE** — process (entanglement) infidelity `1−F_e` of a CPTP map / unitary error | Schumacher PRA 54, 2614 (1996) (`F_e` def + Kraus form `Σ_k|Tr(ρE_k)|²`); Nielsen arXiv:quant-ph/0205035 (Eq. 3 `F_avg=(d F_e+1)/(d+1)`; **Eq. 16** operator-basis `F_e=|Tr U/d|²` for unitary U) | **DIRECT** | `…/schumacher_nielsen_entanglement_fidelity_quant-ph-0205035.md` | `forward/joint_lindbladian.py:_choi_state_from_kraus`, `_state_fidelity`, `assemble_substep_channel` |
| M29 canonical definition | — | — | `docs/error_mechanisms.md` line 120 (M29 = 2q `exp(−i ε ZX/2)` unitary, "**cross-resonance-like ZX residue**" — the repo's own label independently corroborates the Magesan grounding) + `2q_parasitic_coupling_hamiltonians_theoretical_derivation.md` §M29 (`H_M29 = J_zx Z⊗X`, "controlled-X / CNOT generator … major source of CNOT errors") | `mechanisms/catalog.py:35` (`"M29": "coherent_zx_parasitic_coupling"`), `catalog.py:282` (`dimensions=["axis_zx", …]`) |

**Why the OPERATOR viewpoint clears the (a)-class threshold (≥2 DIRECT close-read; ≥2 DIRECT-*physical*).**
The bar is now met with **two independent device-real references — theory AND measurement — for the SAME
`Z⊗X` interaction**: **≥2 DIRECT-physical: Magesan 1804.04073 (CR theory) + Sheldon 1603.04821 (CR
measurement), both device-real ZX.** Three independent DIRECT close-reads license a *pure* `Z⊗X` coherent
generator, TWO of them device-direct (not merely algebra-direct): (i) **Magesan–Gambetta** (device THEORY)
— `Z⊗X` is THE entangling term of the cross-resonance gate, written explicitly as a Pauli-tensor
coefficient (Eq. 3.16, `H_CR = … − (JΩ/√(Δ²+Ω²)) ZX/2`; Eq. 3.14 gives `tr(H_CR·ZX/2)`), with the
realistic-transmon ZX coefficient in closed form (Eq. 4.26) and the full {IX,IZ,ZI,ZX,ZZ} tensor whose
**control-side operator is restricted to {I,Z}** — ZX is the *unique* 2-body entangling term in the CR
family. (i′) **Sheldon–Magesan–Chow–Gambetta arXiv:1603.04821 / PRA 93, 060302(R)** (device MEASUREMENT)
— the **complementary primary source**: the IBM experiment that **measures the full CR Hamiltonian on real
fixed-frequency transmons via Hamiltonian tomography** (Eq. 2 `H = Z⊗A/2 + I⊗B/2`), extracting `ZX` (and
the five other terms `{IX,IY,IZ,ZX,ZY,ZZ}`) directly from the control-conditioned target x-Rabi rates,
`ZX = (Ω⁰_x − Ω¹_x)/2` — the **measured** counterpart of Magesan's theoretical `tr(H_CR·ZX/2)`. Together
these two are the strongest possible primary-source license for M29: a real superconducting two-qubit
gate's interaction Hamiltonian IS `∝ ZX` both in closed-form theory (Magesan) and in direct device
measurement (Sheldon), and *parasitic ZX* (un-echoed / crosstalk-induced) is the named residual error.
(ii) **Zhang** — `σ¹_z⊗σ²_x` is the 7th
listed basis element of the non-local part `p` of su(4) (Eq. 7, verbatim), and the general anisotropic
interaction `H = ½ Σ_ab J_ab σ_a⊗σ_b` with **independent** cross-coefficients J_ab is written out as
Example 2 — so a pure single cross-axis ZX is the one-coordinate point of the su(4) non-local basis. The
three INDIRECT device-physics notes bound the claim and anchor the magnitude: a *pure* ZX is the **driven /
cross-resonance** axis (Magesan), distinct from the **always-on transverse XX** of a gmon coupler (Geller —
no driven ZX in the bare coupler) and the **always-on parasitic ZZ** (Mundada); the Kraus–Cirac diagonal-`d`
canonical form shows ZX is an *off-diagonal* (anisotropic, cross-term) axis that local dressing rotates into
the XX/YY/ZZ Cartan frame. **Realistic parasitic magnitude:** the CR ZX rate is **a few MHz** at tens-of-MHz
drive (Magesan Fig.1/Fig.3, `J/2π=3.8 MHz`, ZX a few-MHz), and the *residual* (parasitic, un-echoed) ZX is a
fraction of that → `J_zx ≈ 2π × (0.1–3) MHz ≈ 10⁻⁴–10⁻² rad/ns`; over a ~20–400 ns CR-gate/idle substep
`ε = J_zx·dt` lands in 10⁻³–10⁻¹.
The OBSERVABLE viewpoint clears threshold from the same DIRECT Schumacher/Nielsen close-read the
M6/M7/M20/M22/M23 ledgers use (the `1−F_e=|Tr U/d|²` closed form is generator-agnostic; only the trace
value changes, and for any traceless Pauli-pair it is `4cos(ε/4)`, §2 B1). **operator_threshold_met = true
(3 DIRECT, ≥2 DIRECT-*physical* — Magesan ZX-is-the-CR-entangler [device THEORY] + Sheldon 1603.04821
ZX-measured-via-Hamiltonian-tomography [device MEASUREMENT] + Zhang Eq.7 ZX∈`p` / Ex.2 independent cross-J;
both Magesan and Sheldon are device-real ZX — the bar is met with two independent device refs, theory +
measurement); observable_threshold_met = true (1 DIRECT, exceeds the 1-DIRECT+3-INDIRECT floor and matches
the 2-DIRECT spirit via the M6/M7/M20/M22/M23 precedent).** ⇒ epistemic_class='a',
implement-from-equations gate PASSES.

**Sibling-symmetry note (why M29 is NOT new physics over M22/M23 at the cert level).** M29 is to M22/M23
exactly what M20 (RY) is to M6 (RX): the SAME cert machinery (Zhang Eq.7 non-local basis / the traceless
Pauli-pair involution closed forms), the SAME observable, with only the Pauli-pair selector changed to
`(Z,X)`. The carrier already lowers `COH_ZX` via the identical `_coherent_family_generator` path with
`pairs=(("Z","X"),)` (`axis1_mcwf_mps_execution.py` line 1082-1083). **The ONE physics distinction that
the cert must encode** (vs the symmetric M22/M23): ZX is **asymmetric under qubit swap** (`Z⊗X ≠ X⊗Z`,
the latter is M31), so the wrong-axis control set must include **XZ(=M31)** as the load-bearing
swap-partner separator — the analogue of the M22↔M23 X↔Y separation, but here a left↔right swap rather
than an axis flip. Per the light-weight-path rule a single-builder + reviewer pass is appropriate (the
heavy ≥3-builder split is reserved for novel physics, which M29's cert is not).

## 1. The mechanism (anchored; REUSE existing carrier code)

**M29 = coherent_zx_parasitic_coupling = a 2q `exp(−i ε ZX/2)` coherent unitary error**
(`docs/error_mechanisms.md` line 120, "cross-resonance-like ZX residue"), the parasitic ZX coupling between two
computational qubits — physically the **cross-resonance entangler** (control-Z ⊗ target-X) or its residual
un-echoed component. It is the **single pure-ZX cross-axis** of the non-local su(4) algebra (Zhang Eq. 7,
the 7th basis element of `p`; the off-diagonal anisotropic point of Kraus–Cirac's `σ_A^T d σ_B`), and is
*device-physically* the dominant two-qubit interaction term of a CR gate (Magesan Eq. 3.16 `H_CR ∝ ZX`) —
the coherent 2-body parasitic term the twin's teacher composes with stochastic Pauli. Per the 2q-Hamiltonian
derivation §M29 it is the **conditional-X / CNOT generator** ("the strength of the X rotation on the target
depends on the Z state of the control"), and parasitic ZX is "a major source of CNOT errors".

**Carrier form (the operator under test — REUSE, do not rebuild):** family `COH_ZX` (in
`TWO_SITE_COHERENT_FAMILIES`, `axis1_mcwf_mps_execution.py` line 84), lowered by
`_hamiltonian_matrix_for_term` (line 883; dispatch `if family in COHERENT_PAULI_FAMILIES`, line 934) →
`_embed_coherent_generator` (line 1104; level-selective embed of the 4×4 onto the computational levels
{0,1}×{0,1}, zero on leaked levels ≥2) → `_coherent_family_generator` (line 1011; `pairs=(("Z","X"),)`
for `COH_ZX`, line 1082-1083, returning `(0.25·coeff)·(Z⊗X)`). On the **4-dim computational subspace**:

```
H_M29 = (coeff / 4) · (Z ⊗ X) ,   Z = [[1,0],[0,-1]], X = [[0,1],[1,0]]   # rad/ns; embedded with the zero generator on any leaked level
        (Z⊗X)² = I₄ ,  eigenvalues ±1 each ×2 ,  Tr(Z⊗X)=0 ,  Z⊗X is REAL-SYMMETRIC and ASYMMETRIC-under-swap (Z⊗X ≠ X⊗Z=M31)
```

**M29-specific structural fact (the two places ZX differs from XX/YY at the matrix level):**
(a) `Z⊗X` is **REAL-SYMMETRIC** (Z is real-diagonal, X is real-symmetric, so the Kronecker product is real
and symmetric — derivation-check: imag-part norm 0, `‖Z⊗X−(Z⊗X)ᵀ‖=0`), with the **specific block-signed
structure**
```
Z⊗X = [[ 0,  1,  0,  0],
       [ 1,  0,  0,  0],
       [ 0,  0,  0, -1],
       [ 0,  0, -1,  0]]          # the |0·> block is +X, the |1·> block is -X (the conditional-X signature)
```
i.e. an off-diagonal X on each control-block with the sign **set by the control qubit's Z eigenvalue** (+1
on `|0·⟩`, −1 on `|1·⟩`) — the literal "conditional X rotation" the §M29 derivation describes.
(b) `Z⊗X` is **ASYMMETRIC under qubit swap**: `Z⊗X ≠ X⊗Z` (the latter is M31; derivation-check:
`‖Z⊗X−X⊗Z‖=2.83 ≠ 0`). [Both class (a) — exact algebraic facts.] It is still traceless with `(Z⊗X)²=I₄`,
so the **scalar `1−F_e` is identical to M22/M23's `sin²(ε/4)`** — the axis/asymmetry difference is invisible
to `1−F_e` and visible ONLY to the operator-identity gate B4. The realized error gate over a substep `dt` is

```
U_M29 = exp(−i · H_M29 · dt) = exp(−i (ε/4) (Z⊗X))
      = cos(ε/4)·I₄ − i·sin(ε/4)·(Z⊗X) ,         ε ≡ coeff · dt   (rad)
```

**Convention bridge (catalog ↔ carrier, declared so the factor is auditable).** `error_mechanisms.md`
writes M29 as `exp(−i ε_cat ZX/2)` (catalog angle `ε_cat`); the carrier's `(coeff/4)(Z⊗X)` gives
`exp(−i(ε/4)(Z⊗X))` with `ε=coeff·dt`. These are the **same gate** with `ε_cat = ε/2` — i.e. the
factor `1/4 = (1/2)²` is the two-qubit over-rotation convention `R_{PQ}(ε_cat)=exp(−i(ε_cat/2)(P⊗Q))`
applied to the carrier's `ε`-per-tensor (carrier docstring line 1026-1029, 1033-1036). The cert sweeps
`ε=coeff·dt` (the carrier's native angle); all closed forms below are in `ε`. [Class (c) — a convention
statement, identical to M22/M23.] **Note on the device convention:** Magesan's CR Hamiltonian carries
the system-Hamiltonian 1/2 (`ZX/2`), so its angle and the carrier's `ε`-per-tensor differ by the same
factor-2; the cert's `ε` is the carrier-native angle and is NOT claimed equal to Magesan's `JΩt/√(…)` —
the device equation grounds the *operator form* `∝ ZX`, the carrier sets the *angle convention*.

**Swept range (NOT a frozen constant):** `ε ∈ {3e-1, 1e-1, 3e-2, 1e-2, 3e-3, 1e-3}` rad. Physical anchor:
the CR ZX rate is **a few MHz** (Magesan, `J/2π=3.8 MHz`, ZX a few-MHz at tens-of-MHz drive); the
*parasitic / residual* (un-echoed, crosstalk-induced) ZX is a fraction of the activated rate, so
`J_zx ≈ 2π×(0.1–3) MHz ≈ 10⁻⁴–10⁻² rad/ns`; over a ~20–400 ns substep `ε = J_zx·dt` lands in 10⁻³–10⁻¹,
and the fully-activated CR (gate-ON) reaches `ε` up to ~0.3+. The cert uses `coeff` and `dt_ns`
independently so `ε = coeff·dt` is swept by varying either.

### 1a. RESOLUTION of the COH_* placement ambiguity (ALREADY LANDED with M6 — inherited)

The brief's placement ambiguity was resolved by the M6 work and **M29 inherits the resolution**:
`mechanisms/axis1_primitives.py` lines 19-24 carry the NOTE that `COH_*`/`COHERENT_PAULI_FAMILIES` are
intentionally **NOT** declared there ("advertising it here was a declaration-without-lowering
faithfulness trap, M6 pre-registration §1a"), and that **the sole canonical lowering site for
coherent-generator families is `simulator/axis1_mcwf_mps_execution._hamiltonian_matrix_for_term`** (via
`_embed_coherent_generator`/`_coherent_family_generator`). **The M29 cert imports the operator under test
from `axis1_mcwf_mps_execution._hamiltonian_matrix_for_term` ONLY, never from the `axis1_primitives`
registry, and must NOT import `_coherent_family_generator` / `_embed_coherent_generator` /
`*_COHERENT_FAMILIES`** (the anti-circular namespace gate, enforced by L10) — the same surface the
M6/M7/M20/M22/M23 ledgers and the qutrit-leakage de-circularized cert use. [Class (c) — a build/placement
decision, already executed; no physics claim.]

## 2. Predicted observable (class (b) bands; ANCHORED — `1−F_e`, the RIGHT one, not invented)

**Observable = process (entanglement) infidelity `1 − F_e`** between the substep channel WITH the M29
error knob and the substep channel WITHOUT it (the ideal/no-error reference) — the standard
`axis1_mechanism_completeness_prereg.md` line-98 cert observable (`assemble_substep_channel` →
Choi-state `F_e`). Schumacher/Nielsen def (reading note, Eq. 16 `F_e=|Tr U/d|²` for a unitary error);
for the pure ZX 2-site error vs identity, **with d=4** and `Tr(Z⊗X)=0`, `(Z⊗X)²=I`:

- **(B1) EXACT closed form [b-band, derivable to a-exact]:**
  `Tr(U_M29) = Tr(cos(ε/4)I₄ − i sin(ε/4)(Z⊗X)) = 4cos(ε/4)`, so
  `F_e(U_M29, I) = |Tr(U_M29)/d|² = |4cos(ε/4)/4|² = cos²(ε/4)` ⇒ **`1 − F_e = sin²(ε/4)`**.
  **The factor is /4 not /2** (the 2-site correction, shared with M22/M23): the carrier generator is
  `(coeff/4)(Z⊗X)`, so the half-angle is `ε/4`, NOT the 1-site `ε/2`. (Contrast M6/M7/M20: `sin²(ε/2)`.)
  Predicted: the carrier-side `1−F_e` (via `_choi_state_from_kraus`+`_state_fidelity`) equals `sin²(ε/4)`
  to the Uhlmann-estimator floor (~4e-8), monotone increasing in `|ε|`, **even in ε**
  (`1−F_e(ε)=1−F_e(−ε)`; `F_e(U)=F_e(U†)`).
  *Derivation-check (RTX 5090, 2026-06-29, `outputs/m29_coherent_zx_fe_derivation_check.py`): carrier
  `1−F_e` vs `sin²(ε/4)` agree to band_resid ≤ 5.6e-8 across ε∈{0.3…1e-3}; even-in-ε diff 0.0;
  `Z⊗X` imag-part norm 0.0, symmetric residual 0.0 (the M29 real-symmetric fact confirmed); swap
  residual `‖Z⊗X−X⊗Z‖=2.83` (the asymmetry-under-swap fact confirmed).*
- **(B2) LEADING-ORDER scaling [b-band]:** `1 − F_e ≈ ‖G‖²_F/d` with `G=(ε/4)(Z⊗X)`,
  `‖G‖²_F=Tr(G²)=(ε/4)²·Tr((Z⊗X)²)=(ε/4)²·Tr(I₄)=(ε/4)²·4=ε²/4`, `/d=/4 → ε²/16` (METRICS.md `/d`,
  **d=4** for the 2-site window). Predicted **quadratic** law: `1−F_e ∝ ε²` at small ε;
  `(1−F_e)/ε² → 1/16` as `ε→0`. The exact form deviates from `ε²/16` at `O(ε⁴)` (since
  `sin²(ε/4)=ε²/16 − ε⁴/(3·256) + …`) — a registered higher-order finding, NOT a carrier bug.
  *Derivation-check: lead `ε²/16` tracks exact with leaddev ε=0.3→1.05e-5, ε=0.1→1.30e-7 (∝ε⁴).*
- **(B3) AVG-GATE link [b-band]:** `1 − F_avg = (d/(d+1))(1−F_e) = (4/5)sin²(ε/4)` — reported as a
  companion ONLY if an RB-comparable number is wanted; `1−F_e` stays the headline (carry the convention
  + the d=4 with the number).

**Statistic flagged INSUFFICIENT (do NOT headline):** `1−F_e` (or `1−F_avg`) is a *scalar average*
measure — coherent and stochastic channels of equal infidelity are indistinguishable by it, AND (the
M29-sharp form) `1−F_e=sin²(ε/4)` is identical for ANY single Pauli-pair generator `P⊗Q`
(`Tr(P⊗Q)=0`, `(P⊗Q)²=I` for Paulis) of the same `ε` — so the scalar `1−F_e` cannot tell **which 2-body
Pauli axis** (ZX vs XX vs YY vs ZZ vs XZ …) the coupling is about, **cannot tell M29 (ZX) from its
swap-partner M31 (XZ)**, and **cannot detect the conditional-X sign structure** (reading-note Limitations;
the surface-code analogue is the Bravyi twirl-underestimate, `correcting_coherent_errors_surface_1710.02270.md`).
The cert therefore ALSO gates the **direct operator/generator identity** (B4 below), the structural witness
`1−F_e` alone cannot provide — and for M29 the operator gate is the SOLE thing that distinguishes ZX from
the other 8 two-body axes (M22/M23/M28/M30-M33/M10), the **M29↔M31 (ZX↔XZ) swap separation included**.

- **(B4) OPERATOR identity [a-exact, the load-bearing gate]:** the carrier generator equals the
  hand-typed reference: `‖H_carrier − H_ref‖_F ≤ 1e-12` and `‖U_carrier − U_ref‖_F ≤ 1e-10`, with
  `H_carrier` Hermitian (`‖H−H†‖_F ≤ 1e-12`) and traceless (`|Tr H| ≤ 1e-12`), where
  `H_ref = (coeff/4)(Z⊗X)`. A miss is a CARRIER PHYSICS BUG — the finding a `1−F_e`-only or circular
  cert could never surface. **For M29 this gate is load-bearing in a way it is not for a scalar cert:**
  since `1−F_e` is axis-blind (B1), B4 is the SOLE witness that the carrier couples via Z⊗X and not
  XX/YY/ZZ/XZ/…. M29-sharp: `Z⊗X` is real-symmetric with the **specific block-signed structure** above
  (off-diagonal X on each control-block, sign `+1`/`−1` set by the control's Z eigenvalue) — an `X⊗X`
  reference (all-`+1` anti-diagonal, no block-sign), a `Y⊗Y` (anti-diagonal signs `−1,+1,+1,−1`), a `Z⊗Z`
  (diagonal), the swap-partner `X⊗Z`(=M31, X-block structure flipped to act on the *target* control), or
  the `XX+YY` of M10 are each caught by B4 immediately (derivation-check: XX/YY/ZZ/XZ/ZY each diff 7.07e-2,
  M10 diff 8.66e-2 at ε=0.1 — all ≫ 1e-3). **The `X⊗Z`(=M31) control is the gate that separates M29 from
  its swap-partner M31.**

## 3. Independent ground truth (non-circular) — the HAND-TYPED reference operator

The reference is **hand-typed in the cert from the literature equations**, importing NO carrier symbol
(`_coherent_family_generator`, `_embed_coherent_generator`, `TWO_SITE_COHERENT_FAMILIES`,
`COHERENT_PAULI_FAMILIES` appear NOWHERE in the cert's executable code). The carrier side imports ONLY
`_hamiltonian_matrix_for_term` (the object under test) — exactly the de-circularized
`axis1_qutrit_leakage_certification` / M6 / M7 / M20 / M22 / M23 ledger pattern
(`test_axis1_wc_decircularized.py`, `test_m6_…`, `test_m22_…`, `test_m23_coherent_cyy_constraint_ledger.py`).

**Reference operator spec (PROVENANCE-carried, transcribed not invented):**

```
# M29 reference generator on the 4-dim computational subspace ({0,1}x{0,1}), zero generator on leaked levels.
# H_M29 = (coeff/4) * (sigma_z (x) sigma_x).
#   sigma_z = [[1,0],[0,-1]],  sigma_x = [[0,1],[1,0]]        <- Pauli Z,X, standard (Nielsen & Chuang Eq. 2.1).
#   Z (x) X is the pure-ZX 2-body generator: THE cross-resonance entangler, written as a Pauli-tensor
#               coefficient  H_CR = (Delta - sqrt(Delta^2+Omega^2)) ZI/2 - (J Omega / sqrt(Delta^2+Omega^2)) ZX/2
#               (Magesan-Gambetta arXiv:1804.04073 Eq. 3.16; Eq. 3.14 tr(H_CR . ZX/2) = -J Omega/sqrt(...);
#                realistic ZX coeff Eq. 4.26; control-side restricted to {I,Z} so ZX is the unique entangler),
#               AND the 7th basis element of the non-local part p of su(4)
#               (Zhang-Vala-Sastry-Whaley arXiv:quant-ph/0209120 Eq. 7: p = span(i/2){..., sigma^1_z sigma^2_x, ...};
#                Sec. V Ex. 2 general anisotropic H = (1/2) Sum_ab J_ab sigma_a(x)sigma_b with independent J_ab).
#   DEVICE origin (cross-resonance, DIRECT): the driven CR entangler; parasitic/residual (un-echoed,
#               crosstalk-induced) ZX is the named CNOT-error source. NOT the gmon always-on transverse
#               coupler (pure XX, Geller arXiv:1405.1915) nor the always-on parasitic ZZ (Mundada arXiv:1810.04182).
#   factor 1/4 = (1/2)^2: two-qubit over-rotation convention  R_{PQ}(eps_cat) = exp(-i (eps_cat/2)(P(x)Q)),
#               carrier eps = coeff*dt is the per-tensor angle; catalog eps_cat = eps/2
#               (error_mechanisms.md "exp(-i eps ZX/2)"; carrier docstring lines 1026-1029).
#   M29 structural facts: Z(x)X is REAL-SYMMETRIC (imag part 0), with the block-signed structure
#               [[0,1,0,0],[1,0,0,0],[0,0,0,-1],[0,0,-1,0]] (off-diag X per control-block, sign +1 on |0.> / -1 on |1.>),
#               and ASYMMETRIC under qubit swap: Z(x)X != X(x)Z (= M31).
def ref_H_M29(coeff, dim_pair, device):       # dim_pair=(d0,d1), each 2 (or 3 if qutrit carrier)
    Z = tensor([[1,0],[0,-1]], complex128, device); X = tensor([[0,1],[1,0]], complex128, device)
    gen4 = 0.25 * coeff * kron(Z, X)          # 4x4 on the {0,1}x{0,1} block; real-symmetric, block-signed
    out = zeros((d0*d1, d0*d1), complex128, device)
    embed gen4[qrow,qcol] -> out[row,col] for li,ri,lo,ro in {0,1}:    # zero on any level >= 2
        row=lo*d1+ro, col=li*d1+ri, qrow=lo*2+ro, qcol=li*2+ri
    return out
# error unitary:  U = matrix_exp(-1j * dt_ns * H)  ==  cos(eps/4) I4 - i sin(eps/4) (Z(x)X),  eps=coeff*dt.
# EXACT 1-F_e reference (unitary vs identity, d=4):  1 - |Tr(U)/4|^2  ==  sin^2(eps/4).
# LEADING 1-F_e reference:  ||(eps/4)(Z(x)X)||_F^2 / 4  ==  eps^2/16.
```

This is a closed-form theorem (the `exp(−i(ε/4)ZX)` matrix + `F_e=|Tr V/d|²`), independent of the
implementation. A from-scratch numerical confirmation on RTX 5090 already ran
(`outputs/m29_coherent_zx_fe_derivation_check.py`, 2026-06-29): the carrier `COH_ZX` op equals
`(coeff/4)(Z⊗X)` to **opdiff 0** across ε∈{0.3…1e-3} and dim∈{(2,2),(3,3)}; `U` to **≤6.3e-8**;
`sin²(ε/4)` vs the carrier Choi `1−F_e` agree to ≤5.6e-8 (Uhlmann floor); `ε²/16` tracks the exact form
with the predicted `O(ε⁴)` deviation; `H` Hermitian + traceless residuals exactly 0; `1−F_e` even in ε to
0.0; `Z⊗X` imag-part norm 0.0 + symmetric residual 0.0 (real-symmetric confirmed); swap residual 2.83
(asymmetry confirmed); the qutrit (3,3) embed has full opdiff 0, max leaked row/col norm 0, and comp-4-block
== `(coeff/4)ZX` exactly. (That script is a derivation-check, NOT the cert.)

**Wrong-axis negative controls (the controls a `1−F_e`-only / scalar cert structurally CANNOT provide
for M29) — the load-bearing M29 controls, M31 included as the swap-partner separator:** **WRONG-AXIS**
references `H_wrong ∈ {(coeff/4)(X⊗X), (coeff/4)(Y⊗Y), (coeff/4)(Z⊗Z), (coeff/4)(X⊗Z), (coeff/4)(Z⊗Y),
(coeff/4)(X⊗X+Y⊗Y)}` (= M22, M23, the ZZ family, **M31**, M30, M10) must DISAGREE with the carrier:
`‖H_carrier − H_wrong‖_F ≥ 1e-3` (derivation-check at ε=0.1: XX/YY/ZZ/XZ/ZY each diff 7.07e-2 ≥ 1e-3,
M10 diff 8.66e-2 — well above the gate at the swept ε). `Z⊗X`, `X⊗X`, `Y⊗Y`, `Z⊗Z`, `X⊗Z`, `Z⊗Y`,
`X⊗X+Y⊗Y` are distinct 2-body generators; a wrong Pauli-pair is the M29 analogue of the leakage cert's
wrong-level control. **The `X⊗Z` (=M31) control is the load-bearing one for M29**: because `1−F_e` is
identical for M29 and M31 (B1, both traceless Pauli-pair involutions), the ZX-vs-XZ operator disagreement
is the ONLY thing in the cert that distinguishes M29 from its swap-partner M31 — making it strictly
necessary (the M29 analogue of the M22↔M23 XX↔YY separation, here a left↔right swap). A weaker `wrong_unit`
control (treat `coeff` as the angle, dropping the ÷4 → `coeff·(Z⊗X)`, or the 1-site ÷2 → `(coeff/2)(Z⊗X)`)
is retained as second/third controls (derivation-check: 1.5e-1, 5.0e-2). **Show the control trips:** corrupt
the carrier pair map `COH_ZX→(Z,X)` to `(X,Z)` (the swap-partner) or any other pair and confirm the
hand-typed `(Z⊗X)` reference CATCHES it (diff ≥ 1e-3, cert fails), while a reference derived FROM the
corrupted carrier map would mirror it to diff 0 (false-pass) — the C2-falsifier shape of
`test_wc_cert_catches_corrupted_carrier_level_map` / `test_m22_…_broken_wrong_axis_trips`. **The
ZX→XZ corruption is the M29-sharp falsifier**: it is the most plausible real bug (a left/right transpose
in the pair map) and is invisible to `1−F_e`, so only the operator gate + this control catches it.

## 4. Bounded simplifications (declared; unbounded ⇒ STOP)

- **S1 — ZX error treated as a STRICT unitary (pure Hamiltonian, no collapse).** Class (a) on the
  certified slice: M29 is by definition a coherent unitary (`docs/error_mechanisms.md` line 120); the cert
  certifies the Hamiltonian generator + the exact `exp(−iHdt)` gate. Error vs faithful: 0 (it IS the
  faithful object). ⇒ **STRICT gate tier** `1−F_e ≤ 1e-6` and operator identities `≤ 1e-12/1e-10`
  (no collapse ⇒ no finite-microstep MCWF error; this is the exact-dense regime, not the GROSS tier).
- **S2 — pure `Z⊗X` in isolation (the device-faithfulness simplification — BOUNDED).** Class (b)/(c):
  device-physically, the cross-resonance interaction is **never pure ZX** — the CR effective Hamiltonian
  carries `ZX` ALONGSIDE `ZI` (the dominant Stark shift), `IX`, `IZ`, and `ZZ` (Magesan Eq. 3.16 / Appendix
  C; the control-side is {I,Z}, target-side {I,X,Z}). A pure-ZX teacher omits the co-occurring ZI/IX/ZZ.
  **Error bound (transcribed):** the largest co-term is **ZI (the Stark shift), comparable to or larger
  than ZX** (Magesan Fig.2, "diverges quickly"), and **IX is the next-largest** (a finite-anharmonicity
  term, Fig.1/Fig.3); `IZ` and `ZZ` "barely move with drive" (`ZZ` offset = the static `ξ/2π=277 kHz`,
  i.e. ≲10% of a few-MHz ZX). So a *standalone* ZX is the **entangling axis isolated from the local
  Stark/Stark-like dressing** (ZI/IX, which are single-qubit-frame and echo-removable) plus the small
  correlated ZZ. The certified object is the **isolated ZX generator**; the co-occurring ZI/IX (single-body,
  the CTRL_*/COH_R* axes) and the correlated ZZ (the `COH_CROSSTALK_ZZ`/`ZZ` axis) are separate generators
  composed alongside (the carrier separates them). Pure ZX as the *standalone cross-resonance entangling
  axis* is licensed by Zhang Eq. 7 (ZX ∈ `p`) + Ex. 2 (independent cross-J) and is the *physically dominant*
  2-body term (Magesan: control-side {I,Z}, ZX the unique entangler). This simplification is **declared +
  bounded**; it does NOT affect the cert (which tests the ZX generator the carrier emits, exactly), only the
  *physical interpretation* of a pure-ZX teacher. [Magesan Eq. 3.16 / App. C — the full {ZI,ZX,IX,IZ,ZZ}
  tensor; the ZI/IX are local-frame Stark and echo-removable, the residual ZX is the parasitic CNOT-error term.]
- **S3 — 2-level computational subspace per site; zero generator on leaked levels.** Class (a): the M29
  ZX knob acts on the computational `{|0>,|1>}` block of each site; in a qutrit/ququart carrier the
  generator is the same 4×4 `(coeff/4)(Z⊗X)` embedded with the zero generator on any level ≥2 (matches
  `_embed_coherent_generator`, confirmed by the derivation-check dim=(3,3) run: full opdiff 0, leaked
  row/col norm 0). Error vs faithful: 0 within the stated semantics. **M29-specific note:** `exp(−i(ε/4)
  ZX)` leaves any leaked level UNCHANGED (`exp(0)=1` on level ≥2) — M29 imparts NO population/phase to
  leaked levels; any leaked-level coupling is a DIFFERENT mechanism (leakage transport, M34/LEAK_*), not
  M29. Same "identity on leaked levels" simplification as M6/M7/M20/M22/M23 S2/S3. (The *real* CR gate DOES
  populate the `|2⟩` levels via the higher-transmon dressing that produces the finite-anharmonicity IX term
  — that leakage is a SEPARATE mechanism the carrier models on the leakage arm, NOT part of the M29 ZX knob.)
- **S4 — `ε = coeff·dt` constant across the substep (no intra-substep drift).** Class (b): drift of the
  coupling strength ACROSS cycles is M13 = Axis-2 (frozen), not M29. Error bound: `O(Δε/ε)`; within one
  substep with a declared instantaneous `coeff`, exact. Cross-cycle drift is explicitly out of this slice.
- **S5 — `1−F_e` reported via the Uhlmann sqrt/eigh Choi estimator (≈4e-8 floor at d=4).** Class (c):
  the estimator floors at ~4e-8 (documented in `composed_vs_joint_infidelity`; confirmed by the
  derivation-check band_resid ~3-6e-8), so `1−F_e` is reported as the standard-metric companion at that
  resolution; the LOAD-BEARING zero-tolerance gate is the direct operator identity (B4) at 1e-12, not
  the `1−F_e` value. **Note:** at the smallest swept ε (e.g. ε=1e-3 → `sin²(ε/4)≈6.25e-8`) the true
  `1−F_e` is AT the estimator floor (derivation-check: carrier 6.43e-9 vs closed 6.25e-8), so the B1 band
  there is dominated by estimator resolution — the operator gate (opdiff 0) carries the cert there.

## 5. Epistemic status (METRICS-ladder)

- **(a) exact:** the operator identity B4 (`H_carrier = (coeff/4)(Z⊗X)` = hand-typed ref, Hermitian,
  traceless, real-symmetric, block-signed; `U=cos(ε/4)I−i sin(ε/4)ZX`); the closed forms `1−F_e=sin²(ε/4)`
  and `‖G‖²_F/d=ε²/16`; the wrong-axis control disagreements (incl. ZX≠XZ swap-partner); the even-in-ε
  symmetry; the zero-on-leaked-levels embed; the `Z⊗X` real-symmetric + asymmetric-under-swap facts. These
  are theorems/identities — the only class anything is built on.
- **(b) bands:** B1 (carrier `1−F_e` = `sin²(ε/4)` to estimator floor; axis-agnostic scalar), B2
  (quadratic `∝ε²`, ratio →1/16), B3 (`1−F_avg=(4/5)·`), the `O(ε⁴)` exact-vs-leading deviation, and
  the S2 device-interpretation bound (pure-ZX omits the co-occurring ZI≳ZX Stark + IX + ZZ≲10% of the CR
  tensor). A miss is a finding.
- **(c) gates:** STRICT numeric tiers (`1−F_e ≤ 1e-6`, operator `≤ 1e-12/1e-10`, wrong-axis `≥ 1e-3`);
  the placement-fix decision (§1a, inherited); the catalog↔carrier convention bridge (§1); the swept ε grid.
- **Headline verdict stays PROVISIONAL** until the GPU cert runs green AND the corruption-falsifier
  trips. Reportable + go/no-go; nothing is built on it. No Axis-1-completion claim, no METRICS change.

## 6. Build org + gate plan

- **Gate tier:** **STRICT** (`1−F_e ≤ 1e-6`; operator-identity `≤ 1e-12`/unitary `≤ 1e-10`) — M29 is a
  pure-Hamiltonian / exact-dense error (no collapse, no finite-step MCWF). NOT the GROSS+convergence
  tier (that is only for collapse-bearing first-order MCWF). Support size: **2 sites, d=4** (and a
  d=(3,3) embed check that the qutrit-carrier op is the computational-4-block + zero generator on leaked).
- **Independent-operator plan:** hand-typed `ref_H_M29` (§3) in the cert module, importing only
  `_hamiltonian_matrix_for_term` from the carrier; `1−F_e` via `_choi_state_from_kraus`+`_state_fidelity`
  (the channels these helpers build from the per-term op are independent of the carrier's
  grouping/lowering path). Wrong-axis (ZX→XX / YY / ZZ / **XZ** / ZY / XX+YY) + wrong-unit (÷4→×1, ÷4→÷2)
  negative controls — **the ZX→XZ control is the load-bearing M29↔M31 swap separator**; a corruption
  falsifier (carrier pair map `COH_ZX→(Z,X)` corrupted to `(X,Z)` → hand-typed ref catches it; circular
  ref would false-pass). The cert mirrors `outputs/m23_coherent_cyy_parasitic_coupling_cert.py` /
  `tests/test_m23_coherent_cyy_constraint_ledger.py` with: (i) the reference Pauli-pair replaced by
  `(Z⊗X)` on d=4; (ii) the family string `COH_YY→COH_ZX`; (iii) the closed forms unchanged (`sin²(ε/4)`,
  ratio `1/16`, `F_avg` `(4/5)` — IDENTICAL to M22/M23, since all are traceless Pauli-pair involutions);
  (iv) the wrong-axis controls `ZX→XX/YY/ZZ/XZ/ZY/XX+YY` (XZ=M31 is the new load-bearing one); (v) the
  real-symmetric + block-signed + asymmetric-under-swap structural assertions on `Z⊗X`; (vi) L9 the
  leaked-level embed over the 4-computational-level layout (indices {0,1,d1,d1+1} of a d0×d1 space). The
  L1-L10 invariant set carries over verbatim in structure from M22/M23.
- **GPU-only, serialized:** assert `torch.cuda.is_available()`; CUDA-missing fails the collection
  (memory rule). Scripted-execution; the cert lands commit-gated.
- **If built heavy:** M29 introduces NO novel cert physics beyond the landed M6/M7/M20/M22/M23 machinery —
  only the Pauli-pair selector → `(Z,X)` on the already-certified 2-site/d=4/factor-1/4 path, plus the
  M29-specific asymmetry-under-swap control (XZ=M31). Per the light-weight-path rule a **single-builder +
  reviewer** pass is appropriate; the heavy ≥3-disjoint-builder split is reserved for novel physics, which
  M29's cert is not. (M29 is in fact the *best-grounded* member of the family — its operator is the
  device-direct cross-resonance entangler, not an idealized canonical axis.)
