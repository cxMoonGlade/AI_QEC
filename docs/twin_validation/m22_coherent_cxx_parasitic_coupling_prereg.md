# M22 coherent_cxx_parasitic_coupling — Pre-Registration (theory-first, LITERATURE-GROUNDED)

Status: **PRE-REGISTRATION, 2026-06-29.** Predictions written BEFORE the run; a miss is a finding,
not a re-fit. First of the **coherent 2q parasitic-coupling Hamiltonians** group
(`axis1_mechanism_completeness_prereg.md` group 2: M10 xx+yy, **M22 cxx**, M23 cyy, M28 xy, M29 zx,
M30 zy, M31 xz, M32 yz, M33 yx). Sibling-in-machinery to the landed 1q over-rotation knobs M6/M7/M20
(`m6_…`, `m7_…`, `m20_coherent_ry_overrotation_prereg.md`) — **same cert pattern, but a 2-SITE
generator on d=4, factor 1/4 not 1/2, and the load-bearing wrong-axis control is XX-vs-{YY,ZZ,XY,…}**.
Does NOT claim Axis-1 completion and adds NO metric to `docs/METRICS.md` (`1−F_e` already in the ledger).

## 0. Grounding ledger (the corresponding papers — all 精读 + noted)

| sub-axis / item | paper(s) | support | reading note | in-repo code (reuse) |
|---|---|---|---|---|
| **OPERATOR** — pure `X⊗X` as a canonical, independent 2-body coherent generator (the *algebra*) | Zhang–Vala–Sastry–Whaley arXiv:quant-ph/0209120 (Eq. 7 `p`=span of the 9 Pauli⊗Pauli; Eq. 10 Cartan `a`={XX,YY,ZZ}; Eq. 11/16 canonical form `exp{(i/2)(c1 XX+c2 YY+c3 ZZ)}`; Ex. 1(3) Ising pure-YY ⇒ pure-XX by Weyl reflection) | **DIRECT** | `…/zhang_vala_sastry_whaley_weyl_chamber_quant-ph-0209120.md` | — |
| **OPERATOR** — pure `X⊗X` generator written out explicitly (the cleanest one-line license) | Kraus–Cirac arXiv:quant-ph/0011050 (Eq. 12 `U_d=e^{−iσ_A^T d σ_B}`, d diag ⇒ Σ_β α_β σ_β⊗σ_β; **Eq. 24** `U_d=e^{−iα S_x}=cosα·1−i sinα·σ_x⊗σ_x`, `S_x=σ_x⊗σ_x`) | **DIRECT** | `…/kraus_cirac_two_qubit_canonical_quant-ph-0011050.md` | — |
| **OPERATOR** — pure `σ_x⊗σ_x` as the *device-physical* transverse interaction of a real (gmon/Xmon) coupler | Geller-Martinis arXiv:1405.1915 (**Eq. 57** `δH = g σx₁σx₂`, with Eq. 55-56 the position-position ϕ₁ϕ₂→σx⊗σx projection; Eq. 82 induced ZZ≈g²/η; the "no YY in leading projection" result) | **DIRECT** | `…/geller_gmon_tunable_coupler_xx_zz_1405.1915.md` | — |
| **OPERATOR (bounding/INDIRECT)** — where pure XX does *not* come from (CR is ZX), and the device-grounded exchange is XX+YY not pure-XX, + realistic magnitudes | Magesan–Gambetta arXiv:1804.04073 (CR tensor A⊗B, A∈{I,Z}; **no XX**); Sung arXiv:2011.01261 (`g12/2π=5.0 MHz`; exchange `(g/2)(XX+YY)`); Yan arXiv:1803.09813 (Eq. 1/2 `g̃=g₁g₂/Δ+g12`); Mundada arXiv:1810.04182 (Eq. 4 exchange; few-MHz band); Foxen arXiv:2001.08343 (fSim θ-swap = XX+YY) | **INDIRECT** | the five sibling 2q-coupling notes (all 精读) | — |
| **OBSERVABLE** — process (entanglement) infidelity `1−F_e` of a CPTP map / unitary error | Schumacher PRA 54, 2614 (1996) (`F_e` def + Kraus form `Σ_k|Tr(ρE_k)|²`); Nielsen arXiv:quant-ph/0205035 (Eq. 3 `F_avg=(d F_e+1)/(d+1)`; Eq. 16 operator-basis `F_e=|Tr U/d|²` for unitary U) | **DIRECT** | `…/schumacher_nielsen_entanglement_fidelity_quant-ph-0205035.md` | `forward/joint_lindbladian.py:_choi_state_from_kraus`, `_state_fidelity`, `assemble_substep_channel` |
| M22 canonical definition | — | — | `docs/error_mechanisms.md` line 113 (M22 = 2q `exp(−i ε XX/2)` unitary, "parasitic XX coupling") + `2q_parasitic_coupling_hamiltonians_theoretical_derivation.md` §M22 | `mechanisms/catalog.py:MECHANISMS["M22"]` |

**Why the OPERATOR viewpoint clears the (a)-class threshold (≥2 DIRECT close-read).** Three independent
DIRECT close-reads license a *pure* `X⊗X` coherent generator: (i) **Zhang** — `X⊗X` is the first listed
basis element of the non-local part `p` of su(4) (Eq. 7) and one of the three Cartan axes (Eq. 10); pure
single-axis is realized standalone (Ex. 1(3) Ising). (ii) **Kraus–Cirac** — the pure-XX gate is written
out as `e^{−iα σx⊗σx}` (Eq. 24), the cleanest "exp(−iα X⊗X) is a canonical standalone two-qubit gate"
statement. (iii) **Geller** — the *device-physical* origin: the gmon/Xmon tunable coupler's transverse
interaction is **exactly `g σx⊗σx`** (Eq. 57), the very platform family the project's real-Google rung
(R2-lite XZZX/Willow Xmon transmons) lives on. The four INDIRECT notes (Magesan/Sung/Yan/Mundada/Foxen)
bound the claim and anchor the magnitude: a *pure* XX (no YY) is the **always-on transverse-coupler /
canonical-axis** form (Geller), not the **exchange `(g/2)(XX+YY)`** (Sung/Yan/Mundada) nor the **CR ZX**
(Magesan); the realistic parasitic magnitude is **`J_xx ≈ 2π × (1–3) MHz ≈ 10⁻² rad/ns`** (Sung Table I
`g12/2π=5 MHz` → `J_xx=g12/2≈2π×2.5 MHz`). The OBSERVABLE viewpoint clears threshold from the same
DIRECT Schumacher/Nielsen close-read the M6/M7/M20 ledgers use (the `1−F_e=|Tr U/d|²` closed form is
generator-agnostic; only the trace value changes for the 2-site case, §2 B1). **operator_threshold_met =
true (3 DIRECT); observable_threshold_met = true (1 DIRECT, exceeds the 1-DIRECT+3-INDIRECT floor and
matches the 2-DIRECT spirit via the M6/M7/M20 precedent).** ⇒ epistemic_class='a',
implement-from-equations gate PASSES.

### 0a. Grounding framing — pure XX kept as an honest Cartan COMPONENT (USER DECISION 2026-06-30)

**USER DECISION 2026-06-30: "keep pure XX/YY as honest Cartan components."** M22 (pure XX) is retained
as the **XX Cartan-axis COMPONENT of the device-real `XX+YY` exchange** (= M10), NOT as a standalone
claim that an isolated pure-XX is the generic always-on parasitic. Device grounding for this framing:

- The **XX term appears as a measured component in ≥2 device Hamiltonians**: **Sung arXiv:2011.01261**
  (direct transverse exchange `(g/2)(XX+YY)`, measured `g12/2π = 5.0 MHz`) and **Foxen arXiv:2001.08343**
  (fSim θ-swap = `(θ/2)(XX+YY)`) — in both, XX is one half of the device-real flip-flop/exchange block.
- **PLUS Geller-Martinis arXiv:1405.1915** exhibits a **genuine isolated pure-XX gmon coupler**: the
  always-on transverse interaction is `δH = g σ_x⊗σ_x` (Eq. 57), with **no YY in the leading parity
  projection** — i.e. a real device family where the standalone XX axis is the physical coupling.
- ⇒ **pure-XX-in-isolation is a bounded (c)-class Cartan idealization** with a genuine device home (the
  gmon coupler) *and* a device-real composite home (the XX half of the exchange). This is **DISTINCT
  from the deleted off-Cartan terms** (XY/YX/XZ/YZ/ZY), which have **NO device home at all** — those were
  removed precisely because no device Hamiltonian exhibits them as a coupling; pure XX is kept because it
  does have one. (Extends/cross-references S2 below, which bounds the pure-XX-vs-XX+YY simplification
  quantitatively; the present note states the *grounding rationale* for keeping it.)

## 1. The mechanism (anchored; REUSE existing carrier code)

**M22 = coherent_cxx_parasitic_coupling = a 2q `exp(−i ε XX/2)` coherent unitary error**
(`docs/error_mechanisms.md` line 113), the parasitic transverse XX coupling between two computational
qubits. It is the **single pure-XX Cartan axis** of the non-local su(4) algebra (Zhang Eq. 7/10, Kraus–
Cirac Eq. 24), and is *physically* the always-on transverse interaction of a gmon/Xmon coupler
(`δH = g σx⊗σx`, Geller Eq. 57) — the coherent 2-body parasitic term the twin's teacher composes with
stochastic Pauli.

**Carrier form (the operator under test — REUSE, do not rebuild):** family `COH_XX` (in
`TWO_SITE_COHERENT_FAMILIES`, `axis1_mcwf_mps_execution.py` line 81), lowered by
`_hamiltonian_matrix_for_term` (line 883; dispatch `if family in COHERENT_PAULI_FAMILIES`, line 934) →
`_embed_coherent_generator` (line 1083; level-selective embed of the 4×4 onto the computational levels
{0,1}×{0,1}, zero on leaked levels ≥2) → `_coherent_family_generator` (line 1011; `pairs=(("X","X"),)`
for `COH_XX`, lines 1053-1080, returning `(0.25·coeff)·(X⊗X)`). On the **4-dim computational subspace**:

```
H_M22 = (coeff / 4) · (X ⊗ X) ,   X = [[0,1],[1,0]]   # rad/ns; embedded with the zero generator on any leaked level
        (X⊗X)² = I₄ ,  eigenvalues ±1 each ×2 ,  Tr(X⊗X)=0
```

so the realized error gate over a substep `dt` is

```
U_M22 = exp(−i · H_M22 · dt) = exp(−i (ε/4) (X⊗X))
      = cos(ε/4)·I₄ − i·sin(ε/4)·(X⊗X) ,         ε ≡ coeff · dt   (rad)
```

**Convention bridge (catalog ↔ carrier, declared so the factor is auditable).** `error_mechanisms.md`
writes M22 as `exp(−i ε_cat XX/2)` (catalog angle `ε_cat`); the carrier's `(coeff/4)(X⊗X)` gives
`exp(−i(ε/4)(X⊗X))` with `ε=coeff·dt`. These are the **same gate** with `ε_cat = ε/2` — i.e. the
factor `1/4 = (1/2)²` is the two-qubit over-rotation convention `R_{PQ}(ε_cat)=exp(−i(ε_cat/2)(P⊗Q))`
applied to the carrier's `ε`-per-tensor (carrier docstring line 1026-1029). The cert sweeps `ε=coeff·dt`
(the carrier's native angle); all closed forms below are in `ε`. [Class (c) — a convention statement.]

**Swept range (NOT a frozen constant):** `ε ∈ {3e-1, 1e-1, 3e-2, 1e-2, 3e-3, 1e-3}` rad (≈ the
parasitic-coupling regime: Sung/Yan/Mundada put `J_xx ≈ 2π×(1–3) MHz ≈ 10⁻² rad/ns`, so over a ~20 ns
substep `ε = J_xx·dt·(factor)` lands in this band; the activated/gate-ON coupler reaches tens of MHz,
`ε` up to ~0.3+). The cert uses `coeff` and `dt_ns` independently so `ε = coeff·dt` is swept by varying
either.

### 1a. RESOLUTION of the COH_* placement ambiguity (ALREADY LANDED with M6 — inherited)

The brief's placement ambiguity was resolved by the M6 work and **M22 inherits the resolution**:
`mechanisms/axis1_primitives.py` lines 19-24 carry the NOTE that `COH_*`/`COHERENT_PAULI_FAMILIES` are
intentionally **NOT** declared there ("advertising it here was a declaration-without-lowering
faithfulness trap, M6 pre-registration §1a"), and that **the sole canonical lowering site for
coherent-generator families is `simulator/axis1_mcwf_mps_execution._hamiltonian_matrix_for_term`** (via
`_embed_coherent_generator`/`_coherent_family_generator`). **The M22 cert imports the operator under test
from `axis1_mcwf_mps_execution._hamiltonian_matrix_for_term` ONLY, never from the `axis1_primitives`
registry, and must NOT import `_coherent_family_generator` / `_embed_coherent_generator` /
`*_COHERENT_FAMILIES`** (the anti-circular namespace gate, enforced by L10) — the same surface the
M6/M7/M20 ledgers and the qutrit-leakage de-circularized cert use. [Class (c) — a build/placement
decision, already executed; no physics claim.]

## 2. Predicted observable (class (b) bands; ANCHORED — `1−F_e`, the RIGHT one, not invented)

**Observable = process (entanglement) infidelity `1 − F_e`** between the substep channel WITH the M22
error knob and the substep channel WITHOUT it (the ideal/no-error reference) — the standard
`axis1_mechanism_completeness_prereg.md` line-98 cert observable (`assemble_substep_channel` →
Choi-state `F_e`). Schumacher/Nielsen def (reading note, Eq. 16 `F_e=|Tr U/d|²` for a unitary error);
for the pure XX 2-site error vs identity, **with d=4** and `Tr(X⊗X)=0`, `(X⊗X)²=I`:

- **(B1) EXACT closed form [b-band, derivable to a-exact]:**
  `Tr(U_M22) = Tr(cos(ε/4)I₄ − i sin(ε/4)(X⊗X)) = 4cos(ε/4)`, so
  `F_e(U_M22, I) = |Tr(U_M22)/d|² = |4cos(ε/4)/4|² = cos²(ε/4)` ⇒ **`1 − F_e = sin²(ε/4)`**.
  **The factor is /4 not /2** (the M22-specific correction): the carrier generator is `(coeff/4)(X⊗X)`,
  so the half-angle is `ε/4`, NOT the 1-site `ε/2`. (Contrast M6/M7/M20: `sin²(ε/2)`.) Predicted: the
  carrier-side `1−F_e` (via `_choi_state_from_kraus`+`_state_fidelity`) equals `sin²(ε/4)` to the
  Uhlmann-estimator floor (~4e-8), monotone increasing in `|ε|`, **even in ε**
  (`1−F_e(ε)=1−F_e(−ε)`: over- and under-rotation of equal magnitude are equally infidel; `F_e(U)=F_e(U†)`).
  *Derivation-check (RTX 5090, 2026-06-29, scratchpad `m22_fe_derivation_check.py`): carrier `1−F_e` vs
  `sin²(ε/4)` agree to band_resid ≤ 6.3e-8 across ε∈{0.3…1e-3}; even-in-ε diff 0.0.*
- **(B2) LEADING-ORDER scaling [b-band]:** `1 − F_e ≈ ‖G‖²_F/d` with `G=(ε/4)(X⊗X)`,
  `‖G‖²_F=Tr(G²)=(ε/4)²·Tr((X⊗X)²)=(ε/4)²·Tr(I₄)=(ε/4)²·4=ε²/4`, `/d=/4 → ε²/16` (METRICS.md `/d`,
  **d=4** for the 2-site window). Predicted **quadratic** law: `1−F_e ∝ ε²` at small ε;
  `(1−F_e)/ε² → 1/16` as `ε→0`. The exact form deviates from `ε²/16` at `O(ε⁴)` (since
  `sin²(ε/4)=ε²/16 − ε⁴/(3·256) + …`) — a registered higher-order finding, NOT a carrier bug.
  *Derivation-check: lead `ε²/16` tracks exact with leaddev ε=0.3→1.05e-5, ε=0.1→1.30e-7 (∝ε⁴).*
- **(B3) AVG-GATE link [b-band]:** `1 − F_avg = (d/(d+1))(1−F_e) = (4/5)sin²(ε/4)` — reported as a
  companion ONLY if an RB-comparable number is wanted; `1−F_e` stays the headline (carry the convention
  + the d=4 with the number).

**Statistic flagged INSUFFICIENT (do NOT headline):** `1−F_e` (or `1−F_avg`) is a *scalar average*
measure — coherent and stochastic channels of equal infidelity are indistinguishable by it, AND (the
M22-sharp form of the caveat) `1−F_e=sin²(ε/4)` is identical for ANY single Pauli-pair generator
`P⊗Q` (`Tr(P⊗Q)=0`, `(P⊗Q)²=I` for Paulis) of the same `ε` — so the scalar `1−F_e` cannot tell **which
2-body Pauli axis** (XX vs YY vs ZZ vs XY vs ZX …) the coupling is about (reading-note Limitations; the
surface-code analogue is the Bravyi twirl-underestimate, `correcting_coherent_errors_surface_1710.02270.md`).
The cert therefore ALSO gates the **direct operator/generator identity** (B4 below), the structural
witness `1−F_e` alone cannot provide — and for M22 the operator gate is the SOLE thing that distinguishes
XX from the other 8 two-body axes (M23/M28-M33/M10).

- **(B4) OPERATOR identity [a-exact, the load-bearing gate]:** the carrier generator equals the
  hand-typed reference: `‖H_carrier − H_ref‖_F ≤ 1e-12` and `‖U_carrier − U_ref‖_F ≤ 1e-10`, with
  `H_carrier` Hermitian (`‖H−H†‖_F ≤ 1e-12`) and traceless (`|Tr H| ≤ 1e-12`), where
  `H_ref = (coeff/4)(X⊗X)`. A miss is a CARRIER PHYSICS BUG — the finding a `1−F_e`-only or circular
  cert could never surface. **For M22 this gate is load-bearing in a way it is not for a scalar cert:**
  since `1−F_e` is axis-blind (B1), B4 is the SOLE witness that the carrier couples via X⊗X and not
  YY/ZZ/XY/…. M22-sharp: `X⊗X` is real-symmetric with zero diagonal — a `Y⊗Y` reference (imaginary
  pattern), `Z⊗Z` (diagonal), `X⊗Y` (mixed), or the `XX+YY` of M10 is caught by B4 immediately
  (derivation-check: YY/ZZ/XY/half/wrong-unit controls all disagree by ≥ 2.5e-3 at ε=0.1).

## 3. Independent ground truth (non-circular) — the HAND-TYPED reference operator

The reference is **hand-typed in the cert from the literature equations**, importing NO carrier symbol
(`_coherent_family_generator`, `_embed_coherent_generator`, `TWO_SITE_COHERENT_FAMILIES`,
`COHERENT_PAULI_FAMILIES` appear NOWHERE in the cert's executable code). The carrier side imports ONLY
`_hamiltonian_matrix_for_term` (the object under test) — exactly the de-circularized
`axis1_qutrit_leakage_certification` / M6 / M7 / M20 ledger pattern (`test_axis1_wc_decircularized.py`,
`test_m6_coherent_rx_constraint_ledger.py`, `test_m7_…`, `test_m20_…`).

**Reference operator spec (PROVENANCE-carried, transcribed not invented):**

```
# M22 reference generator on the 4-dim computational subspace ({0,1}x{0,1}), zero generator on leaked levels.
# H_M22 = (coeff/4) * (sigma_x (x) sigma_x).
#   sigma_x = [[0,1],[1,0]]                            <- Pauli-X, standard (Nielsen & Chuang Eq. 2.1).
#   X (x) X is the pure-XX 2-body generator: a basis element of the non-local part p of su(4)
#               (Zhang-Vala-Sastry-Whaley arXiv:quant-ph/0209120 Eq. 7; Cartan axis, Eq. 10), and the
#               explicit standalone gate  U_d = e^{-i alpha (X(x)X)} = cos a . 1 - i sin a . X(x)X
#               (Kraus-Cirac arXiv:quant-ph/0011050 Eq. 24).
#   DEVICE origin: the gmon/Xmon tunable-coupler transverse interaction  dH = g . sigma_x (x) sigma_x
#               (Geller-Martinis arXiv:1405.1915 Eq. 57).
#   factor 1/4 = (1/2)^2: two-qubit over-rotation convention  R_{PQ}(eps_cat) = exp(-i (eps_cat/2)(P(x)Q)),
#               carrier eps = coeff*dt is the per-tensor angle; catalog eps_cat = eps/2
#               (error_mechanisms.md line 113 "exp(-i eps XX/2)"; carrier docstring lines 1026-1029).
def ref_H_M22(coeff, dim_pair, device):       # dim_pair=(d0,d1), each 2 (or 3 if qutrit carrier)
    X = tensor([[0,1],[1,0]], complex128, device)
    gen4 = 0.25 * coeff * kron(X, X)          # 4x4 on the {0,1}x{0,1} block
    out = zeros((d0*d1, d0*d1), complex128, device)
    embed gen4[qrow,qcol] -> out[row,col] for li,ri,lo,ro in {0,1}:    # zero on any level >= 2
        row=lo*d1+ro, col=li*d1+ri, qrow=lo*2+ro, qcol=li*2+ri
    return out
# error unitary:  U = matrix_exp(-1j * dt_ns * H)  ==  cos(eps/4) I4 - i sin(eps/4) (X(x)X),  eps=coeff*dt.
# EXACT 1-F_e reference (unitary vs identity, d=4):  1 - |Tr(U)/4|^2  ==  sin^2(eps/4).
# LEADING 1-F_e reference:  ||(eps/4)(X(x)X)||_F^2 / 4  ==  eps^2/16.
```

This is a closed-form theorem (the `exp(−i(ε/4)XX)` matrix + `F_e=|Tr V/d|²`), independent of the
implementation. A from-scratch numerical confirmation on RTX 5090 already ran (scratchpad
`m22_fe_derivation_check.py`, 2026-06-29): the carrier `COH_XX` op equals `(coeff/4)(X⊗X)` to **opdiff
0** across ε∈{0.3…1e-3} and dim∈{(2,2),(3,3)}; `U` to **≤2.2e-16**; `sin²(ε/4)` vs the carrier Choi
`1−F_e` agree to ≤6.3e-8 (Uhlmann floor); `ε²/16` tracks the exact form with the predicted `O(ε⁴)`
deviation; `H` Hermitian + traceless residuals exactly 0; `1−F_e` even in ε to 0.0; the qutrit (3,3)
embed has full opdiff 0, max leaked row/col norm 0, and comp-4-block == `(coeff/4)XX` exactly. (That
script is a derivation-check, NOT the cert.)

**Wrong-axis negative controls (the controls a `1−F_e`-only / scalar cert structurally CANNOT provide
for M22) — the load-bearing M22 controls:** **WRONG-AXIS** references `H_wrong ∈ {(coeff/4)(Y⊗Y),
(coeff/4)(Z⊗Z), (coeff/4)(X⊗Y), (coeff/4)(X⊗X+Y⊗Y)}` (= M23, the ZZ family, M28, M10) must DISAGREE with
the carrier: `‖H_carrier − H_wrong‖_F ≥ 1e-3` (derivation-check at ε=0.1: YY/ZZ/XY each diff 3.54e-3 ≥
1e-3; well above the gate at the swept ε). `X⊗X`, `Y⊗Y`, `Z⊗Z`, `X⊗Y`, `X⊗X+Y⊗Y` are distinct 2-body
generators; a wrong Pauli-pair is the M22 analogue of the leakage cert's wrong-level control. Because
`1−F_e` is identical for any single Pauli-pair (B1), **these wrong-axis operator controls are the ONLY
thing in the cert that detects a corrupted COH_XX pair map** — making them strictly necessary for M22.
A weaker `wrong_unit` control (treat `coeff` as the angle, dropping the ÷4 → `coeff·(X⊗X)`, or the
1-site ÷2 → `(coeff/2)(X⊗X)`) is retained as second/third controls (derivation-check: 7.5e-3, 2.5e-3).
**Show the control trips:** corrupt the carrier pair map `COH_XX→(X,X)` to `(Y,Y)` (or any other pair)
and confirm the hand-typed `(X⊗X)` reference CATCHES it (diff ≥ 1e-3, cert fails), while a reference
derived FROM the corrupted carrier map would mirror it to diff 0 (false-pass) — the C2-falsifier shape
of `test_wc_cert_catches_corrupted_carrier_level_map` / `test_m7_L3b_broken_wrong_axis_rx_trips`.

## 4. Bounded simplifications (declared; unbounded ⇒ STOP)

- **S1 — XX error treated as a STRICT unitary (pure Hamiltonian, no collapse).** Class (a) on the
  certified slice: M22 is by definition a coherent unitary (`docs/error_mechanisms.md` line 113); the
  cert certifies the Hamiltonian generator + the exact `exp(−iHdt)` gate. Error vs faithful: 0 (it IS
  the faithful object). ⇒ **STRICT gate tier** `1−F_e ≤ 1e-6` and operator identities `≤ 1e-12/1e-10`
  (no collapse ⇒ no finite-microstep MCWF error; this is the exact-dense regime, not the GROSS tier).
- **S2 — pure `X⊗X` with NO correlated `Z⊗Z` (the device-faithfulness simplification — BOUNDED).**
  Class (b)/(c): on the **gmon/Xmon platform** the always-on transverse XX comes paired with an induced
  diagonal `J σz⊗σz`, `J ≈ g²/η` (Geller Eq. 82/88, η/2π≈213 MHz). A *pure* XX teacher (ZZ=0) is an
  idealization. **Error bound (transcribed, not invented):** at `J_xx ≈ 2π×(2–5) MHz`, `g≈2π×(4–10) MHz`
  ⇒ `J_ZZ ≈ g²/η ≈ 2π×(0.1–0.5) MHz` — i.e. the omitted correlated-ZZ generator is **≲ 5–20%** of the
  XX coefficient (tens-of-kHz at a few-MHz XX). The certified object is the **isolated XX generator**;
  the correlated ZZ, if/when modeled, is the separate `COH_ZZ`/`COH_CROSSTALK_ZZ` axis composed
  alongside (the carrier already separates them). This simplification is **declared + bounded**; it does
  NOT affect the cert (which tests the XX generator the carrier emits, exactly), only the *physical
  interpretation* of a pure-XX teacher. [Geller note "Open question"; Sung/Yan/Mundada "pure-XX vs
  XX+YY" caveat — the device-grounded exchange is `(g/2)(XX+YY)` = M22+M23, the pure-XX is the
  canonical-axis idealization licensed by Zhang/Kraus-Cirac.] **See §0a for the grounding rationale**
  (USER DECISION 2026-06-30): pure XX is kept as the honest XX Cartan COMPONENT of the device-real
  `XX+YY` exchange, with a genuine isolated device home (Geller's gmon pure-XX coupler) — distinct from
  the deleted off-Cartan terms (XY/YX/XZ/YZ/ZY), which have no device home at all.
- **S3 — 2-level computational subspace per site; zero generator on leaked levels.** Class (a): the M22
  XX knob acts on the computational `{|0>,|1>}` block of each site; in a qutrit/ququart carrier the
  generator is the same 4×4 `(coeff/4)(X⊗X)` embedded with the zero generator on any level ≥2 (matches
  `_embed_coherent_generator`, confirmed by the derivation-check dim=(3,3) run: full opdiff 0, leaked
  row/col norm 0). Error vs faithful: 0 within the stated semantics. **M22-specific note:** `exp(−i(ε/4)
  XX)` leaves any leaked level UNCHANGED (`exp(0)=1` on level ≥2) — M22 imparts NO population/phase to
  leaked levels; any leaked-level coupling is a DIFFERENT mechanism (leakage transport, M34/LEAK_*), not
  M22. Same "identity on leaked levels" simplification as M6/M7/M20 S2.
- **S4 — `ε = coeff·dt` constant across the substep (no intra-substep drift).** Class (b): drift of the
  coupling strength ACROSS cycles is M13 = Axis-2 (frozen), not M22. Error bound: `O(Δε/ε)`; within one
  substep with a declared instantaneous `coeff`, exact. Cross-cycle drift is explicitly out of this slice.
- **S5 — `1−F_e` reported via the Uhlmann sqrt/eigh Choi estimator (≈4e-8 floor at d=4).** Class (c):
  the estimator floors at ~4e-8 (documented in `composed_vs_joint_infidelity`; confirmed by the
  derivation-check band_resid ~4-6e-8), so `1−F_e` is reported as the standard-metric companion at that
  resolution; the LOAD-BEARING zero-tolerance gate is the direct operator identity (B4) at 1e-12, not
  the `1−F_e` value. **Note:** at the smallest swept ε (e.g. ε=1e-3 → `sin²(ε/4)≈6.25e-8`) the true
  `1−F_e` is AT the estimator floor, so the B1 band there is dominated by estimator resolution — the
  operator gate (opdiff 0) carries the cert there, as for M6/M7/M20.

## 5. Epistemic status (METRICS-ladder)

- **(a) exact:** the operator identity B4 (`H_carrier = (coeff/4)(X⊗X)` = hand-typed ref, Hermitian,
  traceless; `U=cos(ε/4)I−i sin(ε/4)XX`); the closed forms `1−F_e=sin²(ε/4)` and `‖G‖²_F/d=ε²/16`; the
  wrong-axis control disagreements; the even-in-ε symmetry; the zero-on-leaked-levels embed. These are
  theorems/identities — the only class anything is built on.
- **(b) bands:** B1 (carrier `1−F_e` = `sin²(ε/4)` to estimator floor; axis-agnostic scalar), B2
  (quadratic `∝ε²`, ratio →1/16), B3 (`1−F_avg=(4/5)·`), the `O(ε⁴)` exact-vs-leading deviation, and
  the S2 correlated-ZZ magnitude bound (≲5-20% of J_xx). A miss is a finding.
- **(c) gates:** STRICT numeric tiers (`1−F_e ≤ 1e-6`, operator `≤ 1e-12/1e-10`, wrong-axis `≥ 1e-3`);
  the placement-fix decision (§1a, inherited); the catalog↔carrier convention bridge (§1); the swept ε grid.
- **Headline verdict stays PROVISIONAL** until the GPU cert runs green AND the corruption-falsifier
  trips. Reportable + go/no-go; nothing is built on it. No Axis-1-completion claim, no METRICS change.

## 6. Build org + gate plan

- **Gate tier:** **STRICT** (`1−F_e ≤ 1e-6`; operator-identity `≤ 1e-12`/unitary `≤ 1e-10`) — M22 is a
  pure-Hamiltonian / exact-dense error (no collapse, no finite-step MCWF). NOT the GROSS+convergence
  tier (that is only for collapse-bearing first-order MCWF). Support size: **2 sites, d=4** (and a
  d=(3,3) embed check that the qutrit-carrier op is the computational-4-block + zero generator on leaked).
- **Independent-operator plan:** hand-typed `ref_H_M22` (§3) in the cert module, importing only
  `_hamiltonian_matrix_for_term` from the carrier; `1−F_e` via `_choi_state_from_kraus`+`_state_fidelity`
  (the channels these helpers build from the per-term op are independent of the carrier's
  grouping/lowering path). Wrong-axis (XX→YY / ZZ / XY / XX+YY) + wrong-unit (÷4→×1, ÷4→÷2) negative
  controls; a corruption falsifier (carrier pair map `COH_XX→(X,X)` corrupted to `(Y,Y)` → hand-typed
  ref catches it; circular ref would false-pass). The cert mirrors
  `tests/test_m7_coherent_rz_constraint_ledger.py` with: (i) the reference Pauli replaced by `(X⊗X)` on
  d=4; (ii) the family string `COH_RZ→COH_XX`, support `(0,)→(0,1)`, local_dims `(d,)→(d0,d1)`; (iii) the
  closed form `sin²(ε/2)→sin²(ε/4)`, ratio `1/4→1/16`, `F_avg` `(2/3)→(4/5)`; (iv) the wrong-axis
  controls `X/Y→YY/ZZ/XY/XX+YY`; (v) L9 the leaked-level embed over the 4-computational-level layout
  (indices {0,1,d1,d1+1} of a d0×d1 space). The L1-L10 invariant set carries over verbatim in structure.
- **GPU-only, serialized:** assert `torch.cuda.is_available()`; CUDA-missing fails the collection
  (memory rule). Scripted-execution; the cert lands commit-gated.
- **If built heavy:** ≥3 disjoint-ownership builders (reference-operator / cert-wiring /
  control+falsifier) + an un-led reviewer given only this prereg + the artifacts. (M22 introduces no
  novel physics beyond the landed M6/M7/M20 machinery — only the 2-site generator, d=4, and the
  factor-1/4 convention — so a single-builder + reviewer pass is also acceptable per the
  light-weight-path rule; the heavy split is reserved for novel physics, which M22 is not.)
