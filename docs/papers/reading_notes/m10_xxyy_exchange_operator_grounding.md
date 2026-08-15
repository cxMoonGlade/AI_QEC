# M10 X⊗X + Y⊗Y exchange — COMPOSITE operator-grounding cross-note (精读 synthesis)

> **Provenance (2026-06-30):** A CROSS-NOTE synthesizing the close-read (精读) evidence for the
> **M10 = coherent_rxx_ryy_perturbation** OPERATOR (`H_M10 = J_coh·(X⊗X + Y⊗Y)`, the *transverse
> exchange / flip-flop* 2-body coherent generator) from already-committed full-text reading notes. It
> exists because M10 is the **first COMPOSITE** of the 2q parasitic-coupling group — the brief's binding
> instruction is **"XX+YY = fixed combo of M22+M23 — certify as COMPOSITE, not an independent generator."**
> So M10's reference operator is `ref_H_M22 + ref_H_M23` (the sum of two ALREADY-(a)-class-grounded Cartan
> axes), and M10's grounding is the **conjunction** of the M22 (XX) and M23 (YY) operator groundings PLUS a
> distinct, stronger device-physics anchor: XX+YY is the *physically realized* exchange interaction (iSWAP/
> fSim θ-swap), whereas pure XX and pure YY are idealized single Cartan axes. Every claim cites a line in a
> committed full-text note; no new paper is read here. The M10 prereg
> (`docs/twin_validation/m10_coherent_rxx_ryy_perturbation_prereg.md`) cites this synthesis.

## The question this note answers

M22 = pure `X⊗X`, M23 = pure `Y⊗Y` — each a single Cartan axis, each `(a)`-class grounded (Zhang Eq. 7/10
basis-element + Cartan-axis; Kraus–Cirac Eq. 24/26 explicit standalone gate). **M10 is the SUM `X⊗X + Y⊗Y`.**
Two honest questions: (i) is the *composite* `X⊗X + Y⊗Y` itself a literature-licensed standalone 2-body
coherent generator, and (ii) is it MORE or LESS grounded than the two pure axes it is built from? The answer
to both is unusually strong: **XX+YY is the single most device-physically DIRECT 2q coherent generator in the
whole parasitic-coupling group**, because it is *the* transverse exchange / flip-flop / iSWAP / fSim θ-swap
interaction that real superconducting couplers produce — the form Sung MEASURES (`g12/2π=5.0 MHz`) and Foxen
writes as the fSim swap block.

## The COMPOSITE identity (the brief's binding instruction — exact, derivation-checked)

`H_M10 = (coeff/4)(X⊗X + Y⊗Y) = (coeff/4)(X⊗X) + (coeff/4)(Y⊗Y) = H_M22 + H_M23` (at equal `coeff`).
Verified from-scratch on GPU (RTX 5090, `outputs/m10_coherent_rxx_ryy_fe_derivation_check.py`, 2026-06-30):
the carrier `COH_XX_YY` op equals `(coeff/4)(X⊗X+Y⊗Y)` to **opdiff 0.0** and equals `ref_H_M22+ref_H_M23` to
**0.0** across `ε∈{0.3…1e-3}` and dim∈{(2,2),(3,3)}. **M10 is certified as the COMPOSITE — its reference is
the literal sum of the two pure-axis references, NOT an independently-typed new generator.** [Class (a) — an
exact algebraic identity.]

**M10 is the symmetric "flip-flop"/excitation-conserving combination, not just any XX+YY.**
`X⊗X + Y⊗Y = 2(σ⁺⊗σ⁻ + σ⁻⊗σ⁺)` (`σ± = (X±iY)/2`) — the EXCHANGE/swap operator. Its spectrum on the
computational 4-space is `{−2, 0, 0, +2}` (a **2-dimensional kernel** spanned by `|Φ⁺⟩=(|00⟩+|11⟩)/√2` and
`|Ψ⁻⟩=(|01⟩−|10⟩)/√2`), NOT the `{±1}×2` of a single Pauli pair — so **XX+YY is NOT an involution**
(`(XX+YY)² = 2I + 2·XX·YY ≠ I`; derivation-check `(XX+YY)²−I` Fro-norm = 4.47). This is the structural fact
that makes M10's observable distinct from M22/M23 (see §Observable).

## The close-read sources, classified FOR THE COMPOSITE XX+YY

### 1. Zhang–Vala–Sastry–Whaley arXiv:quant-ph/0209120 — **DIRECT** (the composite IS a worked standalone gate)
- **Eq. 7 / Eq. 10:** XX and YY are the first two basis elements of the non-local part `p` of su(4), and the
  first two of the three Cartan axes `a={XX,YY,ZZ}` (reading note `zhang_..._quant-ph-0209120.md` lines
  36-37, 41). The sum of two Cartan generators is a legitimate element of the maximal Abelian subalgebra.
- **Example 1(2) — the XX+YY combination written as a standalone gate.** The reading note records verbatim
  (line 129): *"Ex. 1(2) XY Hamiltonian = ¼(XX+YY) ... explicitly listed standalone Hamiltonian"* and
  (line 131): *"'XX+YY' is the physical exchange combination — both are valid; M22 = the basis element, the
  swap is the M22+M23 sum (= fSim θ-swap of the foxen note)."* So Zhang lists `¼(σ¹ₓσ²ₓ + σ¹ᵧσ²ᵧ)` as an
  explicit standalone two-body interaction Hamiltonian (the "XY interaction" generating the swap line of the
  Weyl chamber). **This is the load-bearing DIRECT statement for M10: the paper writes M10's exact composite
  generator as a worked example, on the same footing as the pure-axis Examples.**
- **Classification: DIRECT.** Zhang writes the XX+YY composite (i) as a sum of two non-local su(4) basis
  elements / Cartan axes (Eq. 7/10) and (ii) as the explicit standalone "XY-interaction" gate `¼(XX+YY)`
  (Example 1(2)). The strongest primary-source license for the composite.

### 2. Foxen et al. arXiv:2001.08343 (Google fSim) — **DIRECT** (XX+YY IS the fSim θ-swap block, device-physical)
- The reading note (`foxen_fsim_twoqubit_gateset_2001.08343.md` line 10, Eq. 1) records verbatim:
  *"`fSim(θ,φ)`: θ=|01⟩↔|10⟩ swap = σXσX+σYσY, φ=|11⟩ phase = σZσZ"*. So the **fSim swap angle θ is generated
  by exactly `X⊗X + Y⊗Y`** — M10's generator IS the fSim θ-block on Sycamore-class gmon transmons (the very
  platform the project's real-Google R2-lite XZZX/Willow rung lives on). The note further records the
  *parasitic* magnitude: a small **residual swap `δθ ≤ 5°`** accumulates as a calibration byproduct of the
  CPHASE family (line 28) — a directly device-grounded magnitude band for a *parasitic* XX+YY.
- **Classification: DIRECT.** Foxen writes M10's exact composite generator as the standard fSim θ-swap
  Hamiltonian block of a real Google two-qubit gate, with a device-measured parasitic magnitude (δθ ≤ 5°).
  This is a device-physical DIRECT that the pure-axis M22/M23 do NOT have (pure XX/YY are idealized single
  axes; the *physical* coupler produces the symmetric XX+YY swap).

### 3. Sung et al. arXiv:2011.01261 (MIT/Lincoln ZZ-free iSWAP) — **DIRECT** (XX+YY = the measured transverse exchange)
- The reading note (`sung_..._2011.01261.md` lines 44, 61-64) records verbatim that the direct qubit–qubit
  exchange is *"`H_xx,direct/ℏ = g12(σ⁺₁σ⁻₂ + σ⁻₁σ⁺₂) = (g12/2)(X₁X₂ + Y₁Y₂)`"* and that the coupler
  *"switches off the effective transverse coupling ... = exactly the transverse σ⁺σ⁻+σ⁻σ⁺ (= XX+YY)
  exchange."* They **MEASURE** the swap rate `|2g̃_iSWAP|/2π` by fitting |100⟩↔|001⟩ excitation-exchange
  oscillations, and report the device magnitude **`g12/2π = 5.0 MHz`** (Table I) ⇒ the XX+YY exchange
  coefficient `J_coh = g12/2 = 2π×2.5 MHz ≈ 0.016 rad/ns` at the always-on floor, tens of MHz when activated.
- **Classification: DIRECT.** Sung writes M10's exact composite generator `(g12/2)(XX+YY)` as the device
  Hamiltonian's transverse exchange term AND measures its coefficient on a real transmon pair. A second
  device-physical DIRECT for the composite. **Note the cross-note verdict in both the Sung note (line 113-118)
  and the Zhang note (line 131): a σ_x⊗σ_x in a real transmon "is most naturally the symmetric half of an
  exchange `(g/2)(XX+YY)` — i.e. it comes paired with an equal Y⊗Y" — so the device-faithful object is M10,
  and pure XX (M22) / pure YY (M23) are the idealized halves.** M10 inherits the device-grounding the pure
  axes had to flag as an idealization.

### 4. Kraus–Cirac arXiv:quant-ph/0011050 — **INDIRECT for the composite** (DIRECT for each pure axis; the sum is the partial Cartan sum)
- Kraus–Cirac give the canonical generator `U_d = e^{−iσ_A^T d σ_B}` with `d` DIAGONAL (Eq. 12) ⇒
  `Σ_β α_β σ_β⊗σ_β`, and write the pure-axis gate `e^{−iα S_x}` (Eq. 24) + name `S_β=σ_β⊗σ_β` as the three
  commuting generators (Eq. 26) (reading note `kraus_cirac_..._quant-ph-0011050.md` lines 50-57). The reading
  note records (line 91-92): *"pure XX (Eq. 24) and the exchange 'XX+YY' combination (achievable as the
  S_x+S_y partial sum) are both legitimate."* So XX+YY = `S_x+S_y` is the `α_x=α_y, α_z=0` point of their
  canonical form — licensed, but as a *partial sum of the diagonal axes*, not written out as a single
  standalone gate the way Eq. 24 writes pure-XX.
- **Classification: INDIRECT for M10** (DIRECT for the components). Kraus–Cirac DIRECTLY licenses each summand
  (XX, YY) as a canonical commuting generator and licenses their sum as the `S_x+S_y` partial Cartan sum; it
  does not write the composite as one explicit example gate (Zhang Ex. 1(2) does that). Honest call:
  component-DIRECT, composite-INDIRECT.

### 5. Geller–Martinis arXiv:1405.1915 + Yan/Mundada — **INDIRECT** (bounding: the gmon always-on term is pure-XX, the *exchange* adds YY)
- Geller: the gmon/Xmon always-on transverse coupler is **pure `g σ_x⊗σ_x`** in the leading parity projection
  — **no YY** (reading note line 67-68). So the *always-on capacitive* coupler is M22 (pure XX), while the
  *transverse exchange* (Sung/Foxen, the flip-flop) is the symmetric XX+YY (= M10). Yan/Mundada anchor the
  same few-MHz transverse-exchange magnitude band.
- **Classification: INDIRECT (bounding).** Establishes WHERE the pure-XX (M22, gmon always-on) ends and the
  XX+YY (M10, transverse exchange/flip-flop) begins, and anchors the magnitude band
  `J ≈ 2π×(0.01–3) MHz ≈ 10⁻⁴–10⁻² rad/ns` (parasitic floor) up to tens of MHz (gate-ON).

### 6. Schumacher (PRA 54, 2614) + Nielsen arXiv:quant-ph/0205035 — **DIRECT** (the observable)
- The `1−F_e = |Tr U/d|²` closed form (Nielsen Eq. 16) is generator-agnostic; the reading note
  (`schumacher_nielsen_..._quant-ph-0205035.md` lines 34, 38) is the OBSERVABLE grounding the whole Axis-1
  mechanism-completeness cert uses. For M10 the trace value differs from the pure axes (eigvals {−2,0,0,2}
  not {±1}, see §Observable), but the *definition* and the Choi-state machinery are identical.
- **Classification: DIRECT (observable).** Same close-read the M6/M7/M20/M22/M23/M28 ledgers use.

## Threshold verdict (LITERATURE-SUPPORT GATE, (a)-class) — applied to BOTH viewpoints

- **OPERATOR viewpoint:** **3 DIRECT close-read (Zhang Ex. 1(2) writes the standalone `¼(XX+YY)` gate;
  Foxen writes XX+YY = the fSim θ-swap block of a real Google gate; Sung writes & MEASURES
  `(g12/2)(XX+YY)` = the device transverse exchange) + ≥2 INDIRECT close-read (Kraus–Cirac `S_x+S_y`
  partial Cartan sum; Geller/Yan/Mundada bounding + magnitude).** Far exceeds the **≥2-DIRECT** branch.
  **operator_threshold_met = true (3 DIRECT).** Stronger than the pure axes M22/M23, because the composite
  XX+YY is the *physically realized* exchange that two real-device experiments (Foxen Google, Sung MIT)
  write out and one measures, whereas pure XX/YY had to flag themselves as idealized single Cartan axes.
- **OBSERVABLE viewpoint (`1−F_e`):** **1 DIRECT (Schumacher/Nielsen, the `F_e=|Tr U/d|²` closed form,
  generator-agnostic) + the M6/M7/M20/M22/M23/M28 precedent.** The closed form transfers verbatim (only the
  eigenvalue spectrum {−2,0,0,2} changes the trace value). **observable_threshold_met = true.**
- ⇒ **epistemic_class = 'a', implement-from-equations gate PASSES** (via a genuine ≥2-DIRECT operator
  branch; the composite is MORE grounded than either pure summand).

## The OBSERVABLE for M10 — distinct from M22/M23 (the composite is NOT just additive in 1−F_e)

Although M10 = M22+M23 at the OPERATOR level, the observable `1−F_e` is **NOT** the sum (nor the same as)
the pure-axis `1−F_e`. With eigvals {−2,0,0,2}, `Tr(U_M10) = e^{iε/2}+1+1+e^{−iε/2} = 2+2cos(ε/2) =
4cos²(ε/4)`, so `F_e = |Tr/4|² = cos⁴(ε/4)`:

> **EXACT: `1 − F_e = 1 − cos⁴(ε/4) = sin²(ε/4)·(2 − sin²(ε/4))`** (ε = coeff·dt; d=4).
> **LEADING: `1 − F_e = ε²/8 − 5ε⁴/768 + O(ε⁶)`** ⇒ QUADRATIC, ratio `(1−F_e)/ε² → 1/8`.

Contrast M22/M23: `1−F_e = sin²(ε/4)`, ratio `1/16`. M10's ratio is `1/8` (TWICE M22's, because two
Cartan axes contribute) and its closed form is `1−cos⁴(ε/4)` (not `sin²`). The leading `‖G‖²_F/d`
formula gives `(ε/4)²·Tr((XX+YY)²)/4 = (ε/4)²·8/4 = ε²/8` — **correct** (matches exact to O(ε⁴)).
Derivation-check (RTX 5090): carrier `1−F_e` vs `1−cos⁴(ε/4)` agree to ≤5.0e-8 (Uhlmann floor); ratio
→0.125. **The scalar `1−F_e` is still axis-blind in the same sense** (it cannot tell XX+YY from, e.g.,
XZ+ZX or any other excitation-preserving exchange of equal ‖G‖) — so the operator-identity gate is the
load-bearing cert, exactly as for the pure axes. But it CAN tell M10 from M22/M23 by the ratio (1/8 vs
1/16) — a registered consequence, not a separator the cert relies on.

## What this changes vs the M22/M23 ledgers
- **M10 is CERTIFIED AS A COMPOSITE**: its reference is `ref_H_M22 + ref_H_M23` (sum of two already-grounded
  Cartan axes), per the brief. It is NOT an independent new generator — there is no new Pauli-pair to ground,
  only the *sum* of two licensed ones plus the device-physics that the sum (not the halves) is the realized
  exchange.
- **M10's grounding is STRONGER than the pure axes** on the device-physics side: 3 DIRECT (Zhang Ex.1(2) +
  Foxen fSim + Sung exchange) vs M22's "pure XX = idealized always-on coupler" / M23's "pure YY = idealized
  anisotropic axis." The composite is the form real couplers produce.
- **M10's observable is DISTINCT** (`1−cos⁴(ε/4)`, ratio 1/8) — the only place the composite is not a trivial
  inheritance of the two halves, and a registered (b)-band finding, derivation-checked.
