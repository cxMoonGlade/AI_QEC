# M23 coherent_cyy_parasitic_coupling — Pre-Registration (theory-first, LITERATURE-GROUNDED)

Status: **PRE-REGISTRATION, 2026-06-29.** Predictions written BEFORE the run; a miss is a finding,
not a re-fit. Second of the **coherent 2q parasitic-coupling Hamiltonians** group
(`axis1_mechanism_completeness_prereg.md` group 2: M10 xx+yy, M22 cxx, **M23 cyy**, M28 xy, M29 zx,
M30 zy, M31 xz, M32 yz, M33 yx). **Direct sibling-in-machinery of the landed M22**
(`m22_coherent_cxx_parasitic_coupling_prereg.md`) — IDENTICAL cert pattern, a 2-SITE generator on d=4,
factor 1/4 not 1/2, **the Y axis instead of X** (exactly as M20=RY is to M6=RX). The load-bearing
wrong-axis control is YY-vs-{XX,ZZ,XY,XX+YY}. Does NOT claim Axis-1 completion and adds NO metric to
`docs/METRICS.md` (`1−F_e` already in the ledger).

## 0. Grounding ledger (the corresponding papers — all 精读 + noted)

| sub-axis / item | paper(s) | support | reading note | in-repo code (reuse) |
|---|---|---|---|---|
| **OPERATOR** — pure `Y⊗Y` as a canonical, independent 2-body coherent generator (the *algebra*); **the literal worked example** | Zhang–Vala–Sastry–Whaley arXiv:quant-ph/0209120 (Eq. 7 `p`=span of the 9 Pauli⊗Pauli; **Eq. 10 Cartan `a`={XX,YY,ZZ}**; Eq. 11/16 canonical form `exp{(i/2)(c1 XX+c2 YY+c3 ZZ)}`; **Ex. 1(3) "Ising Hamiltonian H3 = ¼ σ¹ᵧσ²ᵧ" = pure-YY standalone interaction, generating the Controlled-U line OA1 — this IS M23 literally**) | **ALGEBRA-DIRECT** (su(4) Cartan axis / operator-algebra — **NOT device-physical**; per plan §1 math-basis membership does NOT count toward the ≥2-DIRECT-*physical* gate) | `…/zhang_vala_sastry_whaley_weyl_chamber_quant-ph-0209120.md` (line 67-68: "M23=YY is literally H3 here") | — |
| **OPERATOR** — pure `Y⊗Y` named as one of the three commuting canonical generators | Kraus–Cirac arXiv:quant-ph/0011050 (Eq. 12 `U_d=e^{−iσ_A^T d σ_B}`, d diag ⇒ Σ_β α_β σ_β⊗σ_β over β∈{x,y,z}; **Eq. 26** defines `S_β ≡ σ_β⊗σ_β`, names `S_y=σ_y⊗σ_y` (YY) as one of the three mutually-commuting `[S_x,S_y]=[S_x,S_z]=[S_y,S_z]=0` axes; Eq. 24 the explicit one-axis gate `U_d=e^{−iα S}=cosα·1−i sinα·S` written for `S_x` and stated for `S_β`) | **ALGEBRA-DIRECT** (math-basis; **NOT device-physical**) | `…/kraus_cirac_two_qubit_canonical_quant-ph-0011050.md` (line 54-57, 88: M23=YY, the YY Cartan axis) | — |
| **OPERATOR (bounding/INDIRECT)** — where `Y⊗Y` does/does not come from device-physically: pure-XX coupler has NO YY in the leading projection (so YY is its own anisotropic axis, NOT the always-on gmon term), and the device-grounded *exchange* is `(g/2)(XX+YY)` (YY appears there) | Geller-Martinis arXiv:1405.1915 (Eq. 57 `δH=g σx⊗σx`; **"no YY in the leading parity projection"** — the always-on transverse coupler is XX, not YY); Sung arXiv:2011.01261 (direct exchange `g12(σ⁺σ⁻+σ⁻σ⁺) = (g12/2)(XX+YY)`, `g12/2π=5.0 MHz` measured — the YY appears in the transverse exchange block); Foxen arXiv:2001.08343 (fSim θ-swap = `(θ/2)(XX+YY)`); Yan arXiv:1803.09813 (Eq.1/2 transverse exchange `g̃`); Mundada arXiv:1810.04182 (exchange, few-MHz) | **INDIRECT** | the five sibling 2q-coupling notes (all 精读) | — |
| **OBSERVABLE** — process (entanglement) infidelity `1−F_e` of a CPTP map / unitary error | Schumacher PRA 54, 2614 (1996) (`F_e` def + Kraus form `Σ_k|Tr(ρE_k)|²`); Nielsen arXiv:quant-ph/0205035 (Eq. 3 `F_avg=(d F_e+1)/(d+1)`; **Eq. 16** operator-basis `F_e=|Tr U/d|²` for unitary U) | **DIRECT** | `…/schumacher_nielsen_entanglement_fidelity_quant-ph-0205035.md` | `forward/joint_lindbladian.py:_choi_state_from_kraus`, `_state_fidelity`, `assemble_substep_channel` |
| M23 canonical definition | — | — | `docs/error_mechanisms.md` line 114 (M23 = 2q `exp(−i ε YY/2)` unitary, "parasitic YY coupling") + `2q_parasitic_coupling_hamiltonians_theoretical_derivation.md` §M23 (`H_M23 = J_yy Y⊗Y`) | `mechanisms/catalog.py:MECHANISMS["M23"]` |

**Why the OPERATOR-ALGEBRA viewpoint is grounded (≥2 ALGEBRA-DIRECT close-reads).** ⚠ **GATE NOTE
(2026-06-30, 5-model review):** these two are **operator-algebra** references (math-basis), **NOT
device-physical**. Under the hard ≥2-DIRECT-*physical* gate, **M23 has ZERO isolated-pure-YY device
references** — no superconducting device exhibits an isolated `Y⊗Y` (Geller's coupler has no YY). M23
is therefore **kept ONLY as a (c)-class Cartan COMPONENT** of the device-real `XX+YY` exchange (Sung+
Foxen, INDIRECT/component) whose physical home is **M10** — per §0a and the user's keep decision. It is
explicitly **re-tiered OUT of the "KEPT — ≥2-DIRECT-physical" set** in the completion audit. The two
ALGEBRA-DIRECT close-reads below license the *pure* `Y⊗Y` operator — and one of them gives it as the **literal
worked example**: (i) **Zhang** — `Y⊗Y` is the canonical YY axis of the Cartan subalgebra `a={XX,YY,ZZ}`
(Eq. 10), and pure single-axis YY is realized standalone as **Example 1(3), the "Ising Hamiltonian
`H3 = ¼ σ¹ᵧσ²ᵧ`"** generating the Controlled-U line OA1 — the Zhang reading note states verbatim "M23=YY
is literally H3 here" (line 68). This is the single strongest possible primary-source license for M23:
the paper writes M23's exact generator as a worked example. (ii) **Kraus–Cirac** — `S_y=σ_y⊗σ_y` is named
(Eq. 26) as one of the three mutually-commuting canonical generators `S_β=σ_β⊗σ_β`, β∈{x,y,z}, with the
one-axis gate `e^{−iα S}=cosα·1−i sinα·S` (Eq. 24, written for `S_x`, holding for each commuting `S_β`).
The five INDIRECT device-physics notes bound the claim and anchor the magnitude: a *pure* YY is the
**anisotropic-crosstalk** axis (the 2q-Hamiltonian derivation §M23: inductive crosstalk, `J_ind ≈ 0.01–0.1
MHz`), distinct from the **always-on gmon XX** (Geller — explicitly **no YY in the leading projection**)
and appearing inside the **physical transverse exchange `(g/2)(XX+YY)`** (Sung/Foxen/Yan/Mundada — the YY
half of the flip-flop block); realistic parasitic magnitude `J_yy ≈ 2π × (0.01–3) MHz ≈ 10⁻⁴–10⁻² rad/ns`.
The OBSERVABLE viewpoint clears threshold from the same DIRECT Schumacher/Nielsen close-read the
M6/M7/M20/M22 ledgers use (the `1−F_e=|Tr U/d|²` closed form is generator-agnostic; only the trace value
changes, and for any traceless Pauli-pair it is `4cos(ε/4)`, §2 B1). **operator_threshold_met = true
(2 DIRECT — Zhang Ex.1(3) is M23 verbatim + Kraus-Cirac `S_y`); observable_threshold_met = true (1 DIRECT,
exceeds the 1-DIRECT+3-INDIRECT floor and matches the 2-DIRECT spirit via the M6/M7/M20/M22 precedent).**
⇒ epistemic_class='a', implement-from-equations gate PASSES.

**Sibling-symmetry note (why M23 is NOT new physics over M22).** M23 is to M22 exactly what M20 (RY) is
to M6 (RX): the SAME equation (Zhang Eq.10 Cartan axes / Kraus-Cirac Eq.26 `S_β`), the SAME papers, the
SAME close-reads, with only the Pauli-axis selector flipped X→Y. The carrier already lowers `COH_YY` via
the identical `_coherent_family_generator` path with `pairs=(("Y","Y"),)` (`axis1_mcwf_mps_execution.py`
line 1078-1079). No NEW physics is introduced; only the axis changes. Per the light-weight-path rule a
single-builder + reviewer pass is appropriate (the heavy ≥3-builder split is reserved for novel physics).

### 0a. Grounding framing — pure YY kept as an honest Cartan COMPONENT, with the honest caveat (USER DECISION 2026-06-30)

**USER DECISION 2026-06-30: "keep pure XX/YY as honest Cartan components."** M23 (pure YY) is retained
as the **YY Cartan-axis COMPONENT of the device-real `XX+YY` exchange** (= M10), NOT as a standalone
claim that an isolated pure-YY is a generic device coupling. Device grounding for this framing:

- The **YY term appears as a measured component in ≥2 device Hamiltonians**: **Sung arXiv:2011.01261**
  (direct transverse exchange `(g/2)(XX+YY)`, measured `g12/2π = 5.0 MHz` — YY is the other half of the
  flip-flop block) and **Foxen arXiv:2001.08343** (fSim θ-swap = `(θ/2)(XX+YY)`). In both, YY is one
  half of the device-real exchange.
- **HONEST CAVEAT (the weakest pure-axis case — reported as such):** **NO device paper exhibits an
  isolated pure-YY Hamiltonian.** In particular **Geller-Martinis arXiv:1405.1915's gmon coupler has NO
  YY at all** (the always-on transverse term is pure XX in the leading parity projection — Geller is M22's
  isolated-XX home, and explicitly *not* a YY home). So pure-YY's physical legitimacy is **strictly as the
  YY-component of the device-real exchange (M10)** — it is grounded by the `XX+YY` exchange measurements
  (Sung/Foxen), **NOT by 2 independent pure-YY isolation measurements** (there are none).
- ⇒ pure YY is **declared a bounded (c)-class Cartan idealization** — kept (per the user decision) as the
  honest YY component of the device-real exchange, with its legitimacy explicitly scoped to the composite
  (M10), not to an isolated pure-YY coupling. (**Honesty over padding** — this is the *weakest* pure-axis
  case of the family and must be reported as such: unlike M22, M23 has no genuine isolated device home,
  only the exchange-component home.) This is still **DISTINCT from the deleted off-Cartan terms**
  (XY/YX/XZ/YZ/ZY): those appear in NO device Hamiltonian *at all* (neither isolated nor as an exchange
  component), whereas YY at least appears as a measured half of the device-real `XX+YY` exchange.
  (Extends/cross-references S2 below, which bounds the pure-YY-vs-XX+YY simplification; the present note
  states the *grounding rationale* and the honest caveat for keeping it.)

## 1. The mechanism (anchored; REUSE existing carrier code)

**M23 = coherent_cyy_parasitic_coupling = a 2q `exp(−i ε YY/2)` coherent unitary error**
(`docs/error_mechanisms.md` line 114), the parasitic transverse YY coupling between two computational
qubits. It is the **single pure-YY Cartan axis** of the non-local su(4) algebra (Zhang Eq. 10 + Ex. 1(3)
Ising `H3=¼YY`, Kraus–Cirac Eq. 26 `S_y`), physically the YY component of an anisotropic capacitive/
inductive crosstalk (2q-Hamiltonian derivation §M23) and the YY half of the device transverse exchange
`(g/2)(XX+YY)` (Sung/Foxen) — the coherent 2-body parasitic term the twin's teacher composes with
stochastic Pauli.

**Carrier form (the operator under test — REUSE, do not rebuild):** family `COH_YY` (in
`TWO_SITE_COHERENT_FAMILIES`, `axis1_mcwf_mps_execution.py` line 82), lowered by
`_hamiltonian_matrix_for_term` (line 883; dispatch `if family in COHERENT_PAULI_FAMILIES`, line 934) →
`_embed_coherent_generator` (line 1104; level-selective embed of the 4×4 onto the computational levels
{0,1}×{0,1}, zero on leaked levels ≥2) → `_coherent_family_generator` (line 1011; `pairs=(("Y","Y"),)`
for `COH_YY`, line 1078-1079, returning `(0.25·coeff)·(Y⊗Y)`). On the **4-dim computational subspace**:

```
H_M23 = (coeff / 4) · (Y ⊗ Y) ,   Y = [[0,-i],[i,0]]   # rad/ns; embedded with the zero generator on any leaked level
        (Y⊗Y)² = I₄ ,  eigenvalues ±1 each ×2 ,  Tr(Y⊗Y)=0 ,  Y⊗Y is REAL-SYMMETRIC
```

**M23-specific structural fact (the one place Y differs from X at the matrix level):** although `Y` is
imaginary/antisymmetric, **`Y⊗Y = (iσ_y)⊗… ` is REAL and SYMMETRIC** — the product of two imaginary
matrices is real (`(−i)(−i)=−1` pattern cancels), `(Y⊗Y)_{jk}` has zero imaginary part and equals
`(Y⊗Y)_{kj}` (derivation-check below: imag-part norm 0, `‖Y⊗Y−(Y⊗Y)ᵀ‖=0`). It is still traceless with
`(Y⊗Y)²=I₄`, so the **scalar `1−F_e` is identical to M22's `sin²(ε/4)`** — the axis difference X↔Y is
invisible to `1−F_e` and visible ONLY to the operator-identity gate B4. [Class (a) — an exact algebraic
fact.] The realized error gate over a substep `dt` is

```
U_M23 = exp(−i · H_M23 · dt) = exp(−i (ε/4) (Y⊗Y))
      = cos(ε/4)·I₄ − i·sin(ε/4)·(Y⊗Y) ,         ε ≡ coeff · dt   (rad)
```

**Convention bridge (catalog ↔ carrier, declared so the factor is auditable).** `error_mechanisms.md`
writes M23 as `exp(−i ε_cat YY/2)` (catalog angle `ε_cat`); the carrier's `(coeff/4)(Y⊗Y)` gives
`exp(−i(ε/4)(Y⊗Y))` with `ε=coeff·dt`. These are the **same gate** with `ε_cat = ε/2` — i.e. the
factor `1/4 = (1/2)²` is the two-qubit over-rotation convention `R_{PQ}(ε_cat)=exp(−i(ε_cat/2)(P⊗Q))`
applied to the carrier's `ε`-per-tensor (carrier docstring line 1026-1029, 1033-1036). The cert sweeps
`ε=coeff·dt` (the carrier's native angle); all closed forms below are in `ε`. [Class (c) — a convention
statement, identical to M22.]

**Swept range (NOT a frozen constant):** `ε ∈ {3e-1, 1e-1, 3e-2, 1e-2, 3e-3, 1e-3}` rad. Physical anchor:
the YY parasitic axis is **inductive/anisotropic crosstalk** (2q-Hamiltonian derivation §M23,
`J_ind ≈ 0.01–0.1 MHz`) typically WEAKER than capacitive XX, but the YY component of the device transverse
**exchange** reaches `g12/2 ≈ 2π×2.5 MHz` (Sung `g12/2π=5.0 MHz`); over a ~20 ns substep `ε = J_yy·dt`
lands in this band, and the activated/gate-ON exchange reaches `ε` up to ~0.3+. The cert uses `coeff` and
`dt_ns` independently so `ε = coeff·dt` is swept by varying either.

### 1a. RESOLUTION of the COH_* placement ambiguity (ALREADY LANDED with M6 — inherited)

The brief's placement ambiguity was resolved by the M6 work and **M23 inherits the resolution**:
`mechanisms/axis1_primitives.py` lines 19-24 carry the NOTE that `COH_*`/`COHERENT_PAULI_FAMILIES` are
intentionally **NOT** declared there ("advertising it here was a declaration-without-lowering
faithfulness trap, M6 pre-registration §1a"), and that **the sole canonical lowering site for
coherent-generator families is `simulator/axis1_mcwf_mps_execution._hamiltonian_matrix_for_term`** (via
`_embed_coherent_generator`/`_coherent_family_generator`). **The M23 cert imports the operator under test
from `axis1_mcwf_mps_execution._hamiltonian_matrix_for_term` ONLY, never from the `axis1_primitives`
registry, and must NOT import `_coherent_family_generator` / `_embed_coherent_generator` /
`*_COHERENT_FAMILIES`** (the anti-circular namespace gate, enforced by L10) — the same surface the
M6/M7/M20/M22 ledgers and the qutrit-leakage de-circularized cert use. [Class (c) — a build/placement
decision, already executed; no physics claim.]

## 2. Predicted observable (class (b) bands; ANCHORED — `1−F_e`, the RIGHT one, not invented)

**Observable = process (entanglement) infidelity `1 − F_e`** between the substep channel WITH the M23
error knob and the substep channel WITHOUT it (the ideal/no-error reference) — the standard
`axis1_mechanism_completeness_prereg.md` line-98 cert observable (`assemble_substep_channel` →
Choi-state `F_e`). Schumacher/Nielsen def (reading note, Eq. 16 `F_e=|Tr U/d|²` for a unitary error);
for the pure YY 2-site error vs identity, **with d=4** and `Tr(Y⊗Y)=0`, `(Y⊗Y)²=I`:

- **(B1) EXACT closed form [b-band, derivable to a-exact]:**
  `Tr(U_M23) = Tr(cos(ε/4)I₄ − i sin(ε/4)(Y⊗Y)) = 4cos(ε/4)`, so
  `F_e(U_M23, I) = |Tr(U_M23)/d|² = |4cos(ε/4)/4|² = cos²(ε/4)` ⇒ **`1 − F_e = sin²(ε/4)`**.
  **The factor is /4 not /2** (the 2-site correction, shared with M22): the carrier generator is
  `(coeff/4)(Y⊗Y)`, so the half-angle is `ε/4`, NOT the 1-site `ε/2`. (Contrast M6/M7/M20: `sin²(ε/2)`.)
  Predicted: the carrier-side `1−F_e` (via `_choi_state_from_kraus`+`_state_fidelity`) equals `sin²(ε/4)`
  to the Uhlmann-estimator floor (~4e-8), monotone increasing in `|ε|`, **even in ε**
  (`1−F_e(ε)=1−F_e(−ε)`; `F_e(U)=F_e(U†)`).
  *Derivation-check (RTX 5090, 2026-06-29, `outputs/m23_coherent_cyy_fe_derivation_check.py`): carrier
  `1−F_e` vs `sin²(ε/4)` agree to band_resid ≤ 5.2e-8 across ε∈{0.3…1e-3}; even-in-ε diff 0.0;
  `Y⊗Y` imag-part norm 0.0, symmetric residual 0.0 (the M23 real-symmetric fact confirmed).*
- **(B2) LEADING-ORDER scaling [b-band]:** `1 − F_e ≈ ‖G‖²_F/d` with `G=(ε/4)(Y⊗Y)`,
  `‖G‖²_F=Tr(G²)=(ε/4)²·Tr((Y⊗Y)²)=(ε/4)²·Tr(I₄)=(ε/4)²·4=ε²/4`, `/d=/4 → ε²/16` (METRICS.md `/d`,
  **d=4** for the 2-site window). Predicted **quadratic** law: `1−F_e ∝ ε²` at small ε;
  `(1−F_e)/ε² → 1/16` as `ε→0`. The exact form deviates from `ε²/16` at `O(ε⁴)` (since
  `sin²(ε/4)=ε²/16 − ε⁴/(3·256) + …`) — a registered higher-order finding, NOT a carrier bug.
  *Derivation-check: lead `ε²/16` tracks exact with leaddev ε=0.3→1.05e-5, ε=0.1→1.30e-7 (∝ε⁴).*
- **(B3) AVG-GATE link [b-band]:** `1 − F_avg = (d/(d+1))(1−F_e) = (4/5)sin²(ε/4)` — reported as a
  companion ONLY if an RB-comparable number is wanted; `1−F_e` stays the headline (carry the convention
  + the d=4 with the number).

**Statistic flagged INSUFFICIENT (do NOT headline):** `1−F_e` (or `1−F_avg`) is a *scalar average*
measure — coherent and stochastic channels of equal infidelity are indistinguishable by it, AND (the
M23-sharp form, IDENTICAL to M22) `1−F_e=sin²(ε/4)` is identical for ANY single Pauli-pair generator
`P⊗Q` (`Tr(P⊗Q)=0`, `(P⊗Q)²=I` for Paulis) of the same `ε` — so the scalar `1−F_e` cannot tell **which
2-body Pauli axis** (YY vs XX vs ZZ vs XY vs ZX …) the coupling is about, and **in particular cannot tell
M23 (YY) apart from M22 (XX)** (reading-note Limitations; the surface-code analogue is the Bravyi
twirl-underestimate, `correcting_coherent_errors_surface_1710.02270.md`). The cert therefore ALSO gates the
**direct operator/generator identity** (B4 below), the structural witness `1−F_e` alone cannot provide —
and for M23 the operator gate is the SOLE thing that distinguishes YY from the other 8 two-body axes
(M22/M28-M33/M10), the **M22↔M23 X↔Y separation included**.

- **(B4) OPERATOR identity [a-exact, the load-bearing gate]:** the carrier generator equals the
  hand-typed reference: `‖H_carrier − H_ref‖_F ≤ 1e-12` and `‖U_carrier − U_ref‖_F ≤ 1e-10`, with
  `H_carrier` Hermitian (`‖H−H†‖_F ≤ 1e-12`) and traceless (`|Tr H| ≤ 1e-12`), where
  `H_ref = (coeff/4)(Y⊗Y)`. A miss is a CARRIER PHYSICS BUG — the finding a `1−F_e`-only or circular
  cert could never surface. **For M23 this gate is load-bearing in a way it is not for a scalar cert:**
  since `1−F_e` is axis-blind (B1), B4 is the SOLE witness that the carrier couples via Y⊗Y and not
  XX/ZZ/XY/…. M23-sharp: `Y⊗Y` is real-symmetric with zero diagonal but with the **specific sign pattern**
  `Y⊗Y = [[0,0,0,−1],[0,0,1,0],[0,1,0,0],[−1,0,0,0]]` (anti-diagonal with signs `−1,+1,+1,−1`) — an
  `X⊗X` reference (anti-diagonal all `+1`) is caught by B4 immediately, as are `Z⊗Z` (diagonal),
  `X⊗Y` (imaginary off-anti-diagonal), and the `XX+YY` of M10 (derivation-check: XX/ZZ/XY each diff
  7.07e-2 at ε=0.1, M10 diff 5.00e-2 — all ≫ 1e-3). **This is the gate that separates M23 from M22.**

## 3. Independent ground truth (non-circular) — the HAND-TYPED reference operator

The reference is **hand-typed in the cert from the literature equations**, importing NO carrier symbol
(`_coherent_family_generator`, `_embed_coherent_generator`, `TWO_SITE_COHERENT_FAMILIES`,
`COHERENT_PAULI_FAMILIES` appear NOWHERE in the cert's executable code). The carrier side imports ONLY
`_hamiltonian_matrix_for_term` (the object under test) — exactly the de-circularized
`axis1_qutrit_leakage_certification` / M6 / M7 / M20 / M22 ledger pattern
(`test_axis1_wc_decircularized.py`, `test_m6_…`, `test_m22_coherent_cxx_constraint_ledger.py`).

**Reference operator spec (PROVENANCE-carried, transcribed not invented):**

```
# M23 reference generator on the 4-dim computational subspace ({0,1}x{0,1}), zero generator on leaked levels.
# H_M23 = (coeff/4) * (sigma_y (x) sigma_y).
#   sigma_y = [[0,-i],[i,0]]                            <- Pauli-Y, standard (Nielsen & Chuang Eq. 2.1).
#   Y (x) Y is the pure-YY 2-body generator: the YY axis of the Cartan subalgebra a={XX,YY,ZZ}
#               (Zhang-Vala-Sastry-Whaley arXiv:quant-ph/0209120 Eq. 10), realized standalone as the
#               worked "Ising Hamiltonian H3 = (1/4) sigma_y(x)sigma_y" (Zhang Example 1(3)) = M23 LITERALLY,
#               and named S_y = sigma_y(x)sigma_y, one of the three commuting canonical generators
#               (Kraus-Cirac arXiv:quant-ph/0011050 Eq. 26; one-axis gate Eq. 24
#                U_d = e^{-i alpha S} = cos a . 1 - i sin a . S).
#   DEVICE origin (anisotropic crosstalk, INDIRECT): the YY half of the transverse exchange
#               (g/2)(XX+YY) measured by Sung arXiv:2011.01261 (g12/2pi=5.0 MHz); NOT the gmon always-on
#               term, which is pure XX with NO YY (Geller arXiv:1405.1915, leading parity projection).
#   factor 1/4 = (1/2)^2: two-qubit over-rotation convention  R_{PQ}(eps_cat) = exp(-i (eps_cat/2)(P(x)Q)),
#               carrier eps = coeff*dt is the per-tensor angle; catalog eps_cat = eps/2
#               (error_mechanisms.md line 114 "exp(-i eps YY/2)"; carrier docstring lines 1026-1029).
#   M23 structural fact: Y(x)Y is REAL-SYMMETRIC (imag part 0), anti-diagonal with signs (-1,+1,+1,-1).
def ref_H_M23(coeff, dim_pair, device):       # dim_pair=(d0,d1), each 2 (or 3 if qutrit carrier)
    Y = tensor([[0,-1j],[1j,0]], complex128, device)
    gen4 = 0.25 * coeff * kron(Y, Y)          # 4x4 on the {0,1}x{0,1} block; real-symmetric
    out = zeros((d0*d1, d0*d1), complex128, device)
    embed gen4[qrow,qcol] -> out[row,col] for li,ri,lo,ro in {0,1}:    # zero on any level >= 2
        row=lo*d1+ro, col=li*d1+ri, qrow=lo*2+ro, qcol=li*2+ri
    return out
# error unitary:  U = matrix_exp(-1j * dt_ns * H)  ==  cos(eps/4) I4 - i sin(eps/4) (Y(x)Y),  eps=coeff*dt.
# EXACT 1-F_e reference (unitary vs identity, d=4):  1 - |Tr(U)/4|^2  ==  sin^2(eps/4).
# LEADING 1-F_e reference:  ||(eps/4)(Y(x)Y)||_F^2 / 4  ==  eps^2/16.
```

This is a closed-form theorem (the `exp(−i(ε/4)YY)` matrix + `F_e=|Tr V/d|²`), independent of the
implementation. A from-scratch numerical confirmation on RTX 5090 already ran
(`outputs/m23_coherent_cyy_fe_derivation_check.py`, 2026-06-29): the carrier `COH_YY` op equals
`(coeff/4)(Y⊗Y)` to **opdiff 0** across ε∈{0.3…1e-3} and dim∈{(2,2),(3,3)}; `U` to **≤6.3e-8**;
`sin²(ε/4)` vs the carrier Choi `1−F_e` agree to ≤5.2e-8 (Uhlmann floor); `ε²/16` tracks the exact form
with the predicted `O(ε⁴)` deviation; `H` Hermitian + traceless residuals exactly 0; `1−F_e` even in ε to
0.0; `Y⊗Y` imag-part norm 0.0 + symmetric residual 0.0 (real-symmetric confirmed); the qutrit (3,3) embed
has full opdiff 0, max leaked row/col norm 0, and comp-4-block == `(coeff/4)YY` exactly. (That script is a
derivation-check, NOT the cert.)

**Wrong-axis negative controls (the controls a `1−F_e`-only / scalar cert structurally CANNOT provide
for M23) — the load-bearing M23 controls, M22 included as the sibling separation:** **WRONG-AXIS**
references `H_wrong ∈ {(coeff/4)(X⊗X), (coeff/4)(Z⊗Z), (coeff/4)(X⊗Y), (coeff/4)(X⊗X+Y⊗Y)}` (= **M22**,
the ZZ family, M28, M10) must DISAGREE with the carrier: `‖H_carrier − H_wrong‖_F ≥ 1e-3`
(derivation-check at ε=0.1: XX/ZZ/XY each diff 7.07e-2 ≥ 1e-3, M10 diff 5.00e-2 — well above the gate at
the swept ε). `Y⊗Y`, `X⊗X`, `Z⊗Z`, `X⊗Y`, `X⊗X+Y⊗Y` are distinct 2-body generators; a wrong Pauli-pair
is the M23 analogue of the leakage cert's wrong-level control. **The `X⊗X` (=M22) control is the
load-bearing one for M23**: because `1−F_e` is identical for M22 and M23 (B1), the YY-vs-XX operator
disagreement is the ONLY thing in the cert that distinguishes M23 from its sibling M22 — making it
strictly necessary. A weaker `wrong_unit` control (treat `coeff` as the angle, dropping the ÷4 →
`coeff·(Y⊗Y)`, or the 1-site ÷2 → `(coeff/2)(Y⊗Y)`) is retained as second/third controls
(derivation-check: 1.5e-1, 5.0e-2). **Show the control trips:** corrupt the carrier pair map
`COH_YY→(Y,Y)` to `(X,X)` (or any other pair) and confirm the hand-typed `(Y⊗Y)` reference CATCHES it
(diff ≥ 1e-3, cert fails), while a reference derived FROM the corrupted carrier map would mirror it to
diff 0 (false-pass) — the C2-falsifier shape of `test_wc_cert_catches_corrupted_carrier_level_map` /
`test_m22_…_broken_wrong_axis_trips`.

## 4. Bounded simplifications (declared; unbounded ⇒ STOP)

- **S1 — YY error treated as a STRICT unitary (pure Hamiltonian, no collapse).** Class (a) on the
  certified slice: M23 is by definition a coherent unitary (`docs/error_mechanisms.md` line 114); the
  cert certifies the Hamiltonian generator + the exact `exp(−iHdt)` gate. Error vs faithful: 0 (it IS
  the faithful object). ⇒ **STRICT gate tier** `1−F_e ≤ 1e-6` and operator identities `≤ 1e-12/1e-10`
  (no collapse ⇒ no finite-microstep MCWF error; this is the exact-dense regime, not the GROSS tier).
- **S2 — pure `Y⊗Y` in isolation (the device-faithfulness simplification — BOUNDED).** Class (b)/(c):
  device-physically, a *pure* YY (no co-occurring XX or induced ZZ) is an idealization of an anisotropic
  crosstalk. On the gmon/Xmon platform the leading always-on transverse term has **NO YY at all** (Geller,
  pure XX in the parity projection); YY appears in the **transverse exchange `(g/2)(XX+YY)`** (Sung, where
  it is paired with an equal XX) and in inductive crosstalk (`J_ind ≈ 0.01–0.1 MHz`, 2q-Hamiltonian
  derivation §M23). **Error bound (transcribed):** a faithful *exchange* teacher would emit XX and YY
  together with `J_xx≈J_yy` (the flip-flop block), so a pure-YY teacher omits a co-magnitude XX; this is
  the M10 (XX+YY) mechanism composed alongside (the carrier separates COH_XX, COH_YY, COH_XX_YY). The
  certified object is the **isolated YY generator**; the co-occurring XX, if/when modeled, is the separate
  `COH_XX`/`COH_XX_YY` axis composed alongside. Pure YY as a *standalone Cartan-axis* generator is
  licensed by Zhang Ex. 1(3) (the standalone Ising `H3=¼YY`) and Kraus-Cirac `S_y`. This simplification is
  **declared + bounded**; it does NOT affect the cert (which tests the YY generator the carrier emits,
  exactly), only the *physical interpretation* of a pure-YY teacher. [Zhang Ex.1(3) = the standalone
  license; Sung/Geller "YY lives in the exchange / not the always-on coupler" caveat.] **See §0a for the
  grounding rationale + the HONEST CAVEAT** (USER DECISION 2026-06-30): pure YY is kept as the honest YY
  Cartan COMPONENT of the device-real `XX+YY` exchange, but — unlike M22 — has **no isolated device home**
  (Geller's gmon coupler has NO YY); its legitimacy is strictly as the YY-component of the exchange (M10),
  not 2 independent pure-YY isolation measurements. This is the weakest pure-axis case of the family.
- **S3 — 2-level computational subspace per site; zero generator on leaked levels.** Class (a): the M23
  YY knob acts on the computational `{|0>,|1>}` block of each site; in a qutrit/ququart carrier the
  generator is the same 4×4 `(coeff/4)(Y⊗Y)` embedded with the zero generator on any level ≥2 (matches
  `_embed_coherent_generator`, confirmed by the derivation-check dim=(3,3) run: full opdiff 0, leaked
  row/col norm 0). Error vs faithful: 0 within the stated semantics. **M23-specific note:** `exp(−i(ε/4)
  YY)` leaves any leaked level UNCHANGED (`exp(0)=1` on level ≥2) — M23 imparts NO population/phase to
  leaked levels; any leaked-level coupling is a DIFFERENT mechanism (leakage transport, M34/LEAK_*), not
  M23. Same "identity on leaked levels" simplification as M6/M7/M20/M22 S2/S3.
- **S4 — `ε = coeff·dt` constant across the substep (no intra-substep drift).** Class (b): drift of the
  coupling strength ACROSS cycles is M13 = Axis-2 (frozen), not M23. Error bound: `O(Δε/ε)`; within one
  substep with a declared instantaneous `coeff`, exact. Cross-cycle drift is explicitly out of this slice.
- **S5 — `1−F_e` reported via the Uhlmann sqrt/eigh Choi estimator (≈4e-8 floor at d=4).** Class (c):
  the estimator floors at ~4e-8 (documented in `composed_vs_joint_infidelity`; confirmed by the
  derivation-check band_resid ~4-5e-8), so `1−F_e` is reported as the standard-metric companion at that
  resolution; the LOAD-BEARING zero-tolerance gate is the direct operator identity (B4) at 1e-12, not
  the `1−F_e` value. **Note:** at the smallest swept ε (e.g. ε=1e-3 → `sin²(ε/4)≈6.25e-8`) the true
  `1−F_e` is AT the estimator floor (derivation-check: carrier 4.99e-8 vs closed 6.25e-8), so the B1 band
  there is dominated by estimator resolution — the operator gate (opdiff 0) carries the cert there.

## 5. Epistemic status (METRICS-ladder)

- **(a) exact:** the operator identity B4 (`H_carrier = (coeff/4)(Y⊗Y)` = hand-typed ref, Hermitian,
  traceless, real-symmetric; `U=cos(ε/4)I−i sin(ε/4)YY`); the closed forms `1−F_e=sin²(ε/4)` and
  `‖G‖²_F/d=ε²/16`; the wrong-axis control disagreements (incl. YY≠XX); the even-in-ε symmetry; the
  zero-on-leaked-levels embed; the `Y⊗Y` real-symmetric fact. These are theorems/identities — the only
  class anything is built on.
- **(b) bands:** B1 (carrier `1−F_e` = `sin²(ε/4)` to estimator floor; axis-agnostic scalar), B2
  (quadratic `∝ε²`, ratio →1/16), B3 (`1−F_avg=(4/5)·`), the `O(ε⁴)` exact-vs-leading deviation, and
  the S2 device-interpretation bound (pure-YY omits a co-magnitude XX of the exchange block). A miss is a
  finding.
- **(c) gates:** STRICT numeric tiers (`1−F_e ≤ 1e-6`, operator `≤ 1e-12/1e-10`, wrong-axis `≥ 1e-3`);
  the placement-fix decision (§1a, inherited); the catalog↔carrier convention bridge (§1); the swept ε grid.
- **Headline verdict stays PROVISIONAL** until the GPU cert runs green AND the corruption-falsifier
  trips. Reportable + go/no-go; nothing is built on it. No Axis-1-completion claim, no METRICS change.

## 6. Build org + gate plan

- **Gate tier:** **STRICT** (`1−F_e ≤ 1e-6`; operator-identity `≤ 1e-12`/unitary `≤ 1e-10`) — M23 is a
  pure-Hamiltonian / exact-dense error (no collapse, no finite-step MCWF). NOT the GROSS+convergence
  tier (that is only for collapse-bearing first-order MCWF). Support size: **2 sites, d=4** (and a
  d=(3,3) embed check that the qutrit-carrier op is the computational-4-block + zero generator on leaked).
- **Independent-operator plan:** hand-typed `ref_H_M23` (§3) in the cert module, importing only
  `_hamiltonian_matrix_for_term` from the carrier; `1−F_e` via `_choi_state_from_kraus`+`_state_fidelity`
  (the channels these helpers build from the per-term op are independent of the carrier's
  grouping/lowering path). Wrong-axis (YY→XX / ZZ / XY / XX+YY) + wrong-unit (÷4→×1, ÷4→÷2) negative
  controls — **the YY→XX control is the load-bearing M22↔M23 separator**; a corruption falsifier (carrier
  pair map `COH_YY→(Y,Y)` corrupted to `(X,X)` → hand-typed ref catches it; circular ref would
  false-pass). The cert mirrors `outputs/m22_coherent_cxx_parasitic_coupling_cert.py` /
  `tests/test_m22_coherent_cxx_constraint_ledger.py` with: (i) the reference Pauli replaced by `(Y⊗Y)` on
  d=4; (ii) the family string `COH_XX→COH_YY`; (iii) the closed forms unchanged (`sin²(ε/4)`, ratio
  `1/16`, `F_avg` `(4/5)` — IDENTICAL to M22, since both are traceless Pauli-pair involutions); (iv) the
  wrong-axis controls `YY→XX/ZZ/XY/XX+YY` (XX is the new load-bearing one); (v) the real-symmetric
  structural assertion on `Y⊗Y`; (vi) L9 the leaked-level embed over the 4-computational-level layout
  (indices {0,1,d1,d1+1} of a d0×d1 space). The L1-L10 invariant set carries over verbatim in structure
  from M22.
- **GPU-only, serialized:** assert `torch.cuda.is_available()`; CUDA-missing fails the collection
  (memory rule). Scripted-execution; the cert lands commit-gated.
- **If built heavy:** M23 introduces NO novel physics beyond the landed M6/M7/M20/M22 machinery — only
  the Pauli-axis selector X→Y on the already-certified 2-site/d=4/factor-1/4 path (exactly as M20=RY to
  M6=RX). Per the light-weight-path rule a **single-builder + reviewer** pass is appropriate; the heavy
  ≥3-disjoint-builder split is reserved for novel physics, which M23 is not.
