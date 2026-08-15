# M28 X⊗Y cross-term — operator-grounding cross-note (精读 synthesis)

> **Provenance (2026-06-29):** This is a CROSS-NOTE that synthesizes the close-read (精读) evidence for the
> **M28 = coherent_xy_parasitic_coupling** OPERATOR (`H_M28 = J_xy · X⊗Y`, the cross-axis 2-body coherent
> generator) from FOUR already-committed full-text reading notes. It exists because M28 is the **first
> CROSS-TERM** of the 2q parasitic-coupling group (vs the same-axis M22 XX / M23 YY), and the cross-term's
> grounding is SUBTLY different from the diagonal axes — a distinction the theory-first protocol exists to
> surface. Every claim here cites a line in a committed full-text note; no new paper is read here, this
> note RE-CLASSIFIES the existing close-reads for the cross-term specifically. The M28 pre-registration
> (`docs/twin_validation/m28_coherent_xy_parasitic_coupling_prereg.md`) cites this synthesis.

## The question this note answers
For M22 (XX) / M23 (YY) the operator is a **diagonal Cartan axis** `σ_β⊗σ_β`, β∈{x,y,z}, and the
literature writes it out explicitly as a standalone gate (Kraus–Cirac Eq. 24 `e^{−iα σ_x⊗σ_x}`; Zhang
Ex. 1(3) `H3=¼YY`). For M28 the operator is a **cross-term** `σ_x⊗σ_y` (the off-diagonal of the canonical
bilinear). The honest question: **which papers DIRECTLY license a pure cross-term `X⊗Y` as an independent
2-body coherent generator, and which only license the diagonal axes?**

## The four close-read sources, re-classified FOR THE CROSS-TERM

### 1. Zhang–Vala–Sastry–Whaley arXiv:quant-ph/0209120 — **DIRECT** (the primary)
- **Eq. 7:** the non-local part `p` of su(4) = the span of the **9 Pauli⊗Pauli operators**, EXPLICITLY
  including `σ¹ₓσ²ᵧ` (= X⊗Y = M28) and `σ¹ᵧσ²ₓ` (= Y⊗X = M33) as basis elements. So the cross-term is, by
  the Cartan decomposition, one of the 9 independent 2-body generators of su(4) — not a derived/composite.
  (Reading note `zhang_..._quant-ph-0209120.md` line 36-37 transcribes the full 9-element `p`.)
- **Example 2 / Sec. V.A:** the **generalized anisotropic exchange**
  `H = ½(J_xx σ¹ₓσ²ₓ + J_yy σ¹ᵧσ²ᵧ + J_xy σ¹ₓσ²ᵧ + J_yx σ¹ᵧσ²ₓ)` — an explicit
  `H_int = Σ_{ab} J_ab σ_a⊗σ_b` with **independent coefficients J_ab**, the reading note recording verbatim
  that this *includes the cross-terms σ_x⊗σ_y, σ_y⊗σ_x = our M28/M33* (reading note line 70-72, repeated
  line 109 "the cross-terms XY/ZX/ZY/XZ/YZ/YX (M28–M33)"). **This is the load-bearing DIRECT statement: the
  paper writes the XY cross-term as an independent Hamiltonian term with its own coefficient J_xy.**
- **Classification: DIRECT.** Zhang writes M28's exact generator (`σ_x⊗σ_y`) as (i) a non-local su(4)
  basis element (Eq. 7) and (ii) an independent term of an explicit standalone Hamiltonian (Example 2).
  This is the single strongest primary-source license for the M28 cross-term.

### 2. Kraus–Cirac arXiv:quant-ph/0011050 — **INDIRECT for the cross-term** (DIRECT only for diagonal)
- The canonical form is `U_d = e^{−i σ_A^T d σ_B}` (Eq. 12) — BUT the paper **restricts `d` to a DIAGONAL
  matrix** (source txt `0011050.txt` line 297 "and d is a diagonal matrix"; line 300 "denote the diagonal
  elements of d by α_x, α_y, α_z"). With `d` diagonal, `σ_A^T d σ_B = α_x XX + α_y YY + α_z ZZ` — **only
  the diagonal XX/YY/ZZ axes survive; the cross-terms `σ_a⊗σ_b` (a≠b) are NOT part of their canonical
  form.** The explicit worked gates (Eq. 24 `e^{−iα σ_x⊗σ_x}`, Eq. 26 `S_β=σ_β⊗σ_β`) are the **diagonal
  axes only**.
- **Classification: INDIRECT for M28.** Kraus–Cirac DIRECTLY licenses M22/M23/ZZ (the diagonal Cartan
  axes) but does NOT write the cross-term `σ_x⊗σ_y` as a generator (its `d` is diagonal by construction).
  It supports M28 only INDIRECTLY: it establishes the general 2-body Pauli bilinear `σ_A^T d σ_B` as THE
  canonical interaction content, of which the cross-term is the off-diagonal completion. **A genuinely
  honest call — NOT a DIRECT for the cross-term**, correcting the temptation to borrow M22's
  Kraus-Cirac DIRECT for M28.

### 3. Magesan–Gambetta arXiv:1804.04073 — **INDIRECT** (cross-terms are physical device Hamiltonians; but ZX, not XY)
- The cross-resonance (CR) effective Hamiltonian of a real IBM fixed-frequency-transmon entangling gate is
  written as the **full Pauli⊗Pauli coefficient tensor** `Σ a_{αβ} σ_α⊗σ_β`, and the **dominant entangling
  term is `Z⊗X`** (Eq. 3.16, Eq. 4.25/4.26) — a genuine CROSS-TERM, the physical entangler, measured by
  Hamiltonian tomography (reading note `magesan_..._1804.04073.md` line 56-59, 113-117). This DIRECTLY
  demonstrates that a mixed/cross Pauli-pair generator `σ_α⊗σ_β` (α≠β) is a **real, device-grounded,
  physical coherent 2-body Hamiltonian** — the central physical legitimacy M28 needs.
- BUT the CR control-side is restricted to {I,Z} (reading note line 76-80: "non-zero Pauli coefficients of
  the form A⊗B with A∈{I,Z}"), so the CR tensor produces `ZX` (M29), NOT `XY` (which has X on the control
  side, identically absent in CR). So the SPECIFIC cross-term Magesan writes is ZX, not XY.
- **Classification: INDIRECT for M28.** Strongly supports the *general principle* (cross-terms `σ_α⊗σ_β`
  are physical device generators, and the effective two-qubit Hamiltonian is the full Pauli tensor that
  mathematically contains the XY block) but its explicit cross-term is ZX, not the XY of M28.

### 4. Geller–Martinis arXiv:1405.1915 + Sung/Foxen/Yan/Mundada — **INDIRECT** (bounding: where XY does NOT come from)
- Geller: the gmon/Xmon always-on transverse coupler is **pure `g σ_x⊗σ_x`** in the leading parity
  projection — **NO cross-term, no YY** (reading note `geller_..._1405.1915.md` line 67-68, 113). Sung/
  Foxen/Yan/Mundada: the transverse exchange is the **symmetric `(g/2)(XX+YY)`** flip-flop — also **no
  cross-term** (reading notes; `sung_..._2011.01261.md` line 61-65 etc.). These BOUND M28: a pure cross-term
  `X⊗Y` does NOT arise from the standard symmetric couplers; it is the **anisotropic / directed** crosstalk
  axis (the 2q-Hamiltonian derivation §M28 "Directed crosstalk, A→B capacitive coupling"), which requires
  breaking the symmetric-exchange structure.
- **Classification: INDIRECT (bounding).** They anchor the magnitude band (`J ≈ 2π×(0.01–3) MHz ≈
  10⁻⁴–10⁻² rad/ns` for parasitic 2q couplings) and establish the device-physical boundary (cross-term =
  anisotropic, not the symmetric exchange).

## Threshold verdict (LITERATURE-SUPPORT GATE, (a)-class)
- **OPERATOR viewpoint:** **1 DIRECT (Zhang — Example 2 writes the independent J_xy XY cross-term + Eq. 7
  lists XY in the 9-element non-local su(4) basis) + ≥3 INDIRECT close-read (Kraus–Cirac general bilinear;
  Magesan cross-terms-are-physical / ZX entangler; Geller/Sung/Foxen/Yan/Mundada bounding + magnitude).**
  This meets the **1-DIRECT + ≥3-INDIRECT** branch of the threshold. **It does NOT claim 2 DIRECT** — only
  Zhang is genuinely DIRECT for the cross-term (Kraus–Cirac's `d` is diagonal; Magesan's cross-term is ZX
  not XY); claiming 2 DIRECT would be borrowing M22/M23's diagonal-axis framing, which this note explicitly
  declines to do. **operator_threshold_met = true** (via 1+≥3).
- **OBSERVABLE viewpoint (`1−F_e`):** **1 DIRECT (Schumacher/Nielsen, the `F_e=|Tr U/d|²` closed form,
  generator-agnostic — `schumacher_nielsen_..._quant-ph-0205035.md`)** + the M6/M7/M20/M22/M23 precedent;
  the closed form is independent of which Pauli-pair the generator is, so the observable grounding transfers
  verbatim. **observable_threshold_met = true.**
- ⇒ **epistemic_class = 'a', implement-from-equations gate PASSES** (via the honest 1-DIRECT+≥3-INDIRECT
  operator branch, NOT a borrowed 2-DIRECT).

## What this changes vs the M22/M23 ledgers
M22/M23 claimed **2–3 DIRECT** for the diagonal axes (Kraus–Cirac Eq. 24/26 + Zhang + Geller) — legitimate
there, because the diagonal generators ARE written out explicitly in Kraus–Cirac and Geller. **M28's
cross-term cannot inherit those DIRECTs** (Kraus–Cirac restricts `d` diagonal; Geller is pure-XX with no
cross-term). The honest M28 operator grounding is **1 DIRECT (Zhang Example 2) + ≥3 INDIRECT** — still above
the (a)-class floor, but via the OTHER branch. This re-classification is the load-bearing output of this
note: M28 is grounded, but the grounding is thinner-and-more-careful than the diagonal axes, exactly as the
physics (a cross-term is a sub-leading anisotropy, not the dominant symmetric coupling) would predict.
