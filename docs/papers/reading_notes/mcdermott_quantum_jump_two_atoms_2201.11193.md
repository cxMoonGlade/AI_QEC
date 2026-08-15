# Full-text 精读 (load-bearing §6.1) — C. A. McDermott, "The quantum jump method: photon statistics and macroscopic quantum jumps of two interacting atoms" (arXiv:2201.11193)

> **Provenance (2026-06-30): FULL-TEXT read of §2–3 (the quantum-jump / MCWF method) and §6.1
> (diagonalising the two-atom Lindblad master equation into collective jump operators), the
> load-bearing parts for the M12 MCWF seam.** PDF `outputs/papers/2201.11193.pdf` → txt
> `outputs/papers/2201.11193.txt` (PyMuPDF, 47 pages, ~100k chars). Greek/math glyphs partly
> mangled; equations read via a utf-8 python reader (char offsets noted) and transcribed by hand.
> Figures not pixel-extracted. The driven-single-atom / photon-statistics chapters (§5, §7–8) were
> skimmed; §6.1 (Eqs. 41–46) close-read in full.

---

## Why this note is load-bearing [ours]

The QEC-Twin carrier is **MCWF-on-MPS** (`axis1_mcwf_mps_execution.py`): it samples quantum-jump
trajectories. M12's two-site joint collapse `L = sqrt(gamma_corr)(sigma1^- + sigma2^-)` comes from a
collective dissipator whose `gamma_ij` coefficient matrix has **off-diagonal (cross-damping)
terms**. The MCWF method **requires the dissipator in diagonal Lindblad form** (a list of
independent jump operators `C_m` with `D[rho] = sum_m (C_m rho C_m^dag - (1/2){C_m^dag C_m, rho})`)
— the bare cross-damped form (off-diagonal `gamma_ij`) **cannot be sampled directly**. This paper is
the explicit, worked **recipe for converting the two-atom cross-damped relaxation superoperator into
the diagonal collective jump operators an MCWF simulator can use** (Eqs. 41–46): diagonalize the
Hermitian `gamma` matrix → symmetric/antisymmetric "Uzma" jump operators `C_s, C_a` with rates
`Gamma_s, Gamma_a`. **This is exactly the M12 carrier-seam implementation step**, and it is an
INDIRECT operator anchor (it grounds the operator + its MCWF representation, citing the standard
two-atom relaxation superoperator from Ref. [44]) and a DIRECT method anchor (the quantum-jump/MCWF
unraveling our carrier uses).

---

## Metadata [paper]

- **Author:** Charles A. McDermott (Department of Physics, Durham University, UK).
- **arXiv:** 2201.11193v2 [quant-ph], 9 Feb 2022 (a thesis-style methods report).
- **Type:** methods / pedagogical + numerics (QuTiP-based quantum-jump simulation) of two
  dipole–dipole-coupled atoms, including photon statistics and macroscopic dark periods.
- **System:** two two-level atoms, optionally non-identical (detuning `delta`), dipole–dipole
  coupled `V`, common-bath collective decay.

---

## Executive summary (of the load-bearing section) [paper]

McDermott applies the **quantum-jump method** (MCWF unraveling): the open dynamics is simulated by
sampling individual trajectories under a non-Hermitian effective Hamiltonian `H_eff = H -
(i/2) sum_m C_m^dag C_m` with stochastic jumps `|psi> -> C_m |psi> / ||C_m |psi>||` at rate
`||C_m |psi>||^2`. For TWO atoms the relaxation superoperator (Eq. 41) carries off-diagonal
cross-damping `Gamma_12` (`S^+_1 S^-_2`, `S^+_2 S^-_1` terms). Because the quantum-jump method needs
the dissipator in **diagonal** form (Eq. 6), the cross terms are an obstacle. The resolution
(Eq. 43–46, after Uzma et al. Ref. [44]): the Hermitian coefficient matrix `gamma_ij` is
diagonalized by a **unitary transform of the dipole operators** into **symmetric / antisymmetric
collective jump operators** `U^-_s = (S^-_1 + S^-_2)/sqrt(2)`, `U^-_a = (S^-_1 - S^-_2)/sqrt(2)`,
giving diagonal collapse operators `C_s = sqrt(Gamma_s) U^-_s`, `C_a = sqrt(Gamma_a) U^-_a` with
`Gamma_s = (1/2)(Gamma + Gamma_12)`, `Gamma_a = (1/2)(Gamma - Gamma_12)`. This is the
super/sub-radiant collective decay in MCWF-ready form.

---

## Method (deep) [paper]

### The quantum-jump (MCWF) method (§3) — what our carrier does

- **Diagonal Lindblad form required (Eq. 6):** `d rho/dt = -i[H,rho] + sum_m ( C_m rho C_m^dag -
  (1/2){C_m^dag C_m, rho} )` with the `{C_m}` a list of jump operators.
- **Effective (non-Hermitian) Hamiltonian (§3.1):** `H_eff = H - (i/2) sum_m C_m^dag C_m`; no-jump
  evolution shrinks the norm; a jump `C_m` is selected with probability `prop ||C_m|psi>||^2`, then
  the state is renormalized. [ours: this is precisely the `_nojump_first_order_kraus` +
  `_sample_joint_jump_or_nojump` logic in `axis1_mcwf_mps_execution.py`.]

### Two-atom relaxation superoperator (Eq. 41 — the cross-damped form)

```
L_relax = -(1/2) Gamma    ( S^+_1 S^-_1 rho + rho S^+_1 S^-_1 - 2 S^-_1 rho S^+_1 )
        -(1/2) Gamma_12 ( S^+_1 S^-_2 rho + rho S^+_1 S^-_2 - 2 S^-_2 rho S^+_1 )
        -(1/2) Gamma_12 ( S^+_2 S^-_1 rho + rho S^+_2 S^-_1 - 2 S^-_1 rho S^+_2 )
        -(1/2) Gamma    ( S^+_2 S^-_2 rho + rho S^+_2 S^-_2 - 2 S^-_2 rho S^+_2 )       (41)
```
> [paper] "the cross-terms with the `Gamma_12` cross-damping rate arising from the coupling of the
> bare systems through the vacuum field, where spontaneous emission from one of the atoms influences
> the spontaneous emission of the other."

**Small-separation cross-damping (Eq. 42):** `Gamma_12 = Gamma (mu_hat_1 . mu_hat_2)`.

### The obstacle + the diagonalization (Eqs. 43–46 — THE M12 SEAM RECIPE)

> [paper] "the quantum jump method requires the relaxation superoperator to be written in the
> **diagonal form** of Eq.(6). Hence, the cross-terms in Eq.(41) ... [are] not suitable for
> computation. ... the coefficients `gamma_ij` of Eq.(4) can be arranged to form a **Hermitian, and
> therefore diagonalisable, matrix `gamma`**, ... a unitary transform of the dipole operators ...
> [gives] new symmetrised jump operators ... equivalent to diagonalising `gamma`."

**Symmetrised ("Uzma") collective operators (Eq. 43):**
```
U^+_s = (1/sqrt(2)) ( S^+_1 + S^+_2 ),   U^-_s = (U^+_s)^dag
U^+_a = (1/sqrt(2)) ( S^+_1 - S^+_2 ),   U^-_a = (U^+_a)^dag                              (43)
```

**Diagonalized relaxation superoperator (Eq. 44–45):** in the `U_s, U_a` basis the cross terms
`Gamma_sa, Gamma_as -> 0` (when both atoms have equal coupling `Gamma`), giving
```
L_relax = -(1/2) sum_{m=s,a} Gamma_m ( U^+_m U^-_m rho + rho U^+_m U^-_m - 2 U^-_m rho U^+_m )   (45)
```

**The collective jump operators (Eq. 46 — THE LOAD-BEARING RESULT):**
```
C_s = sqrt(Gamma_s) U^-_s,   Gamma_s = (1/2)(Gamma + Gamma_12)        [symmetric / superradiant]
C_a = sqrt(Gamma_a) U^-_a,   Gamma_a = (1/2)(Gamma - Gamma_12)        [antisymmetric / subradiant]   (46)
```
> [paper] "the collective interactions between the atoms give rise not only to the coherent coupling,
> but also to the **super- and sub-radiant modification of dissipative spontaneous emission rates.**"
> "the diagonalisation above refers specifically to the diagonalisation of the **coefficients
> `gamma_ij`** [NOT a change of the Hamiltonian basis]."

[ours] For the fully-cooperative M12 limit `Gamma_12 -> Gamma`: `Gamma_s -> Gamma`, `Gamma_a -> 0`,
so the symmetric collapse is `C_s = sqrt(Gamma) (S^-_1 + S^-_2)/sqrt(2)` and the antisymmetric is
dark — i.e. the single effective jump `sqrt(Gamma)(sigma^-_1 + sigma^-_2)/sqrt(2)`, matching M12's
`L = sqrt(gamma_corr)(sigma1^- + sigma2^-)` (the `1/sqrt(2)` and the `Gamma_s = (1/2)(...)` factors
are this paper's dissipator-normalization convention; the channel they generate is identical).

---

## The MECHANISM (for implementation) [paper → ours]

This paper is the **MCWF-implementation recipe** for M12, not a new mechanism. The seam in
`axis1_mcwf_mps_execution.py` (`_collapse_operator` / `_sample_joint_jump_or_nojump`, currently
**1-site only**, applying `C` on `where=support[0]`) must be extended so a 2-site collective
collapse term builds the **diagonalized collective jump operators** `C_s, C_a` (Eq. 46) on the
two-site (4x4) joint support and samples among `{NO_JUMP, C_s, C_a}` — i.e. the same jump-or-no-jump
logic, but with the jump operator acting on BOTH sites jointly (a 4x4 gate on `where=(i,j)`), not a
single-site Kraus. The independent oracle `assemble_substep_channel` consumes the dense `c_list`
(the bare or diagonalized collapse operators — equivalent, since it builds the full Liouvillian), so
the cert checks the carrier's diagonalized-jump trajectory channel reproduces the oracle's dense
collective dissipator.

**Parameters:** `Gamma` = single-qubit T1 rate; `Gamma_12 = eta * Gamma`, `eta in [0,1]` the
cooperativity (swept, class (c) — Eq. 42 gives `Gamma_12 = Gamma(mu_hat_1.mu_hat_2)` for free-space
dipoles, geometry-specific, not a transmon magnitude).

---

## The OBSERVABLE / metric [paper]

NOT the M12 substep observable. This paper's observables are photon statistics (`g^(2)(tau)`),
waiting-time distributions, and macroscopic dark-period (jump) visibility — trajectory-level
quantum-optics diagnostics, not the same-substep `1 - F_e`. M12's `1 - F_e` is grounded in
`schumacher_nielsen_entanglement_fidelity_quant-ph-0205035.md`. This note is a method + operator
anchor. (The dark-period physics IS the subradiant `U^-_a` mode being decoupled — a structural
confirmation of the collective jump.)

---

## Findings + numbers [paper]

- **Eq. 41 (cross-damped two-atom relaxation superoperator)** + **Eq. 46 (diagonalized collective
  jump operators `C_s, C_a`, rates `(1/2)(Gamma +/- Gamma_12)`)** — the load-bearing (a)-class
  results.
- **`Gamma_12 = Gamma(mu_hat_1.mu_hat_2)`** at small separation (Eq. 42).
- Pairwise-orthogonality check of the right-eigenstate basis: `||Lambda - I||_F <= 1e-4` across the
  parameter space (Appendix) — a numerical sanity bound, not load-bearing for M12.

---

## Limitations [paper]

- **Free-space atoms (dipole geometry), not SC qubits.** Operator form transfers; the magnitude
  `Gamma_12 = Gamma(mu_hat_1.mu_hat_2)` is free-space-specific (use Cattaneo Eq. A1 for transmons).
- **Two atoms, equal coupling `Gamma` assumed** for the clean diagonalization (`Gamma_sa = Gamma_as
  = 0`); non-identical atoms (`delta != 0`) require the general (non-Hermitian-eigvec) diagonalization
  discussed but not the focus.
- **Methods/thesis report** (not peer-reviewed in the usual sense), but it transcribes the standard
  two-atom relaxation superoperator from Ref. [44] (Uzma et al.) faithfully and the MCWF method from
  the standard references — so it is reliable as a *recipe*, and it cites the primary sources.

---

## Relevance to qec_twin M12 [ours]

1. **The MCWF-seam recipe for the 2-site collective collapse.** Eq. (43)–(46) is exactly how to put
   M12's joint collapse on the quantum-jump carrier: diagonalize `gamma` → collective jumps `C_s,
   C_a` → sample. This grounds the *implementation* the task brief calls for (extend the 1-site
   collapse path to a 2-site joint collapse) — the carrier must build the diagonalized collective
   jumps, not the bare cross-damped form.
2. **INDIRECT operator support** (grounds the collective jump operator + its diagonal form, citing
   the standard relaxation superoperator Ref. [44]) **+ DIRECT method support** (the MCWF/quantum-jump
   unraveling our carrier implements).
3. **Confirms the non-additivity / cross-term physics** (jaschke 1804.09796): the off-diagonal
   `Gamma_12` is what makes the diagonalization necessary — the joint collapse is genuinely
   2-site, not two independent T1 jumps.
4. **Convention bridge:** McDermott's `Gamma_s = (1/2)(Gamma + Gamma_12)` (Eq. 46) vs Ficek's
   `gamma + gamma_12` (Eq. 53) differ by the dissipator-prefactor convention; both generate the same
   physical super/subradiant channel. Carry the convention with the number when certifying.

---

## How to use / trust + open questions [ours]

- **Trust:** high for the diagonalization recipe + the MCWF method (Eq. 41/43–46 read verbatim; the
  collective jump operators `C_s = sqrt(Gamma_s)(S^-_1+S^-_2)/sqrt(2)` etc. are unambiguous). The
  paper cites the standard sources (Uzma et al. Ref [44] for Eq. 41; the quantum-jump method
  references for §3). Glyph mangling resolved via the python reader.
- **Open question (implementation):** the carrier seam should sample among `{NO_JUMP, C_s, C_a}` with
  the joint (4x4) jump operators on `where=(i,j)`; for the fully-cooperative M12 case only `C_s`
  survives (`Gamma_a = 0`), but the general seam should build BOTH eigen-jumps from the diagonalized
  `gamma` matrix so a partial-cooperativity `eta < 1` is representable. Certify the trajectory channel
  vs `assemble_substep_channel` (dense oracle) at GROSS `1 - F_e <= 1e-1` + `O(1/m^2)` convergence as
  `microstep_count` grows (collapse-bearing tier).
