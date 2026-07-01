# Full-text 精读 (load-bearing §IV.A) — Z. Ficek, "Quantum entanglement and disentanglement of multi-atom systems" (arXiv:1002.4124)

> **Provenance (2026-06-30): FULL-TEXT read of the load-bearing two-atom master-equation
> section (§IV.A "Two atoms in free space", Eqs. 47–53).** PDF `outputs/papers/1002.4124.pdf` →
> txt `outputs/papers/1002.4124.txt` (PyMuPDF, 51 pages, ~255k chars). The extractor classifies
> the txt as binary ("data") and mangles greek/math glyphs; sections were located + read via a
> python utf-8 reader (char offsets noted), equations transcribed by hand against the standard
> Lehmberg–Agarwal collective-decay form. This is a long review; only the two-atom collective-decay
> master equation (the M12 operator anchor) was close-read in full — the entanglement-dynamics
> remainder was skimmed. Figures not pixel-extracted.

---

## Why this note is load-bearing [ours]

**M12 = correlated two-qubit relaxation** = the two-site joint collapse
`L = sqrt(gamma_corr)(sigma1^- + sigma2^-)`. The two SC-qubit anchors (Ojanen 0705.1085, Mlynek
1412.2392) give the rate structure but **not** the explicit collective Lindblad master equation
with the cross-damping `gamma_12`. This review writes the **canonical Lehmberg–Agarwal two-atom
master equation** (Eq. 47) — the field-standard, textbook-grade derivation of the collective-decay
dissipator with the cross-damping coefficient `gamma_ij` — and the explicit collective-state rate
equations (Eq. 53) giving the **superradiant rate `gamma + gamma_12` and subradiant rate
`gamma - gamma_12`**. This is the DIRECT, explicit-operator anchor for the collective Dicke jump
that M12 lowers. (The SC-qubit specialization of exactly this form is Cattaneo 2005.06229 Eq. 4.)

---

## Metadata [paper]

- **Author:** Zbigniew Ficek (The National Centre for Mathematics and Physics, KACST, Riyadh).
- **arXiv:** 1002.4124v1 [quant-ph], 22 Feb 2010 (a review article).
- **Type:** review (theory) of multi-atom entanglement; the load-bearing part for us is the
  standard two-atom collective spontaneous-emission master equation (a textbook derivation reviewed
  here, originating Lehmberg PRA 2, 883 (1970) [ref 21] and Agarwal (1974) [ref 22]).
- **PACS:** 03.67.Bg, 03.67.Mn, 42.50.Dv (quantum optics / quantum information).

---

## Executive summary (of the load-bearing section) [paper]

For two two-level atoms in free space coupled to the common vacuum field, the reduced density
matrix obeys the **Lehmberg–Agarwal master equation** (Eq. 47): a Hamiltonian part (free + the
dipole–dipole shift `Omega_ij`) plus a dissipator carrying the **diagonal single-atom decay
`gamma_ii = gamma`** (the Einstein A coefficient) AND the **off-diagonal collective damping
`gamma_ij` (`i != j`)** from incoherent photon exchange between the atoms. In the collective-state
basis (symmetric `|s>`, antisymmetric `|a>`), the populations obey rate equations (Eq. 53) with
**symmetric (superradiant) rate `gamma + gamma_12`** and **antisymmetric (subradiant) rate
`gamma - gamma_12`**. For small interatomic separation `k r_12 << 1`, `gamma_12 -> gamma`, so the
symmetric state becomes superradiant (`-> 2 gamma`, double the single-atom rate) and the
antisymmetric state subradiant (`-> 0`). For large separation the collective effects vanish and the
system reduces to two independent atoms.

---

## Method (deep) [paper]

### The two-atom collective master equation (Eq. 47 — THE LOAD-BEARING EQUATION)

> [paper] "For two two-level atoms interacting in free space with a vacuum field at zero
> temperature, the evolution of the density matrix is given by the **Lehmberg–Agarwal master
> equation** [21, 22]:"

```
d rho / dt = -i (omega0/2) sum_{i=1,2} [ S^z_i , rho ]
           - i sum_{i != j = 1,2} Omega_ij [ S^+_i S^-_j , rho ]
           - (1/2) sum_{i,j=1,2} gamma_ij ( {rho S^+_i, S^-_j} + {S^+_i, S^-_j rho} )      (47)
```
where `S^+_i, S^-_i, S^z_i` are the dipole raising / lowering / population-difference operators of
atom `i`, and (verbatim) **"`gamma_ii ≡ gamma` are the spontaneous decay rates of the atoms, equal
to the Einstein A coefficient."** [The dissipator is written with the (anti)commutator form
`{rho S^+_i, S^-_j} + {S^+_i, S^-_j rho}`; expanding, the standard GKSL form is
`gamma_ij ( S^-_j rho S^+_i - (1/2){S^+_i S^-_j, rho} )` summed over `i,j` — the collective Lindblad
dissipator with the PSD coefficient matrix `gamma_ij`.]

> [paper] "The terms in the master equation that depend on `gamma_ij` and `Omega_ij` (`i != j`) are
> the so-called **collective terms** ... The parameter `gamma_ij` represents the **collective
> damping** which results from an incoherent exchange of photons between the atoms. The collective
> damping leads in general to a change in the lifetime of the collective states from the single-atom
> radiative lifetime. The parameter `Omega_ij` represents the collective shift (dipole–dipole
> interaction)."

### The collective coefficients (Eqs. 48–50)

```
gamma_ij = (3/2) gamma { [1 - (mu_hat . r_hat_ij)^2] sin(k r_ij)/(k r_ij)
                        + [1 - 3(mu_hat . r_hat_ij)^2] ( cos(k r_ij)/(k r_ij)^2 - sin(k r_ij)/(k r_ij)^3 ) }   (48)
Omega_ij = (3/4) gamma { -[1 - (mu_hat . r_hat_ij)^2] cos(k r_ij)/(k r_ij)
                        + [1 - 3(mu_hat . r_hat_ij)^2] ( sin(k r_ij)/(k r_ij)^2 + cos(k r_ij)/(k r_ij)^3 ) }   (49)
```
with `mu_hat` the (parallel) dipole unit vector, `r_hat_ij` the inter-atom direction, `k = omega0/c`.

**Small-separation limit (Eq. 50):** `gamma_ij => gamma [1 - O((k r_ij)^2) + ...]` for `k r_ij << 1`.
> [paper] "For small `k r_ij`, the collective damping `gamma_ij` becomes equal to `gamma` ... For
> large `k r_ij`, the collective effects become negligible and the system reduces to two independent
> atoms."

### Collective-state rate equations (Eq. 53 — THE SUPER/SUBRADIANT RATES)

Collective (Dicke) basis: `|s> = (|eg> + |ge>)/sqrt(2)` (symmetric), `|a> = (|eg> - |ge>)/sqrt(2)`
(antisymmetric), `|4> = |ee>` (doubly excited), `|1> = |gg>`. Populations obey:
```
rho_44_dot = -2 gamma rho_44
rho_ss_dot = -(gamma + gamma_12) (rho_ss - rho_44)
rho_aa_dot = -(gamma - gamma_12) (rho_aa - rho_44)                                       (53)
```
> [paper] "The transitions to and from the **symmetric state occur with an enhanced rate
> `gamma + gamma_12`**, whereas the transitions to and from the **antisymmetric state occur with a
> reduced rate `gamma - gamma_12`**. ... For small `k r_12`, the state `|Psi_s>` becomes
> **superradiant with a decay rate double that of the single atom `gamma`**, and the state
> `|Psi_a>` becomes **subradiant**, with a decay rate of order `(k r_12) gamma` which vanishes in the
> limit of small distances `k r_12 << 1`."

---

## The MECHANISM (for implementation) [paper → ours]

M12's joint collapse is the relaxation part of Eq. (47). [ours] In the collective basis the
dissipator diagonalizes into the symmetric / antisymmetric collective jump operators
```
S^-_sym  = (sigma^-_1 + sigma^-_2)/sqrt(2)   with rate  Gamma_sym  = gamma + gamma_12
S^-_anti = (sigma^-_1 - sigma^-_2)/sqrt(2)   with rate  Gamma_anti = gamma - gamma_12
```
For the small-separation (fully cooperative) limit `gamma_12 -> gamma`: `Gamma_sym -> 2 gamma`,
`Gamma_anti -> 0` ⇒ the ONLY collapse channel is `C_sym = sqrt(2 gamma) S^-_sym =
sqrt(gamma)(sigma^-_1 + sigma^-_2)` = **M12's `L = sqrt(gamma_corr)(sigma1^- + sigma2^-)`** exactly
(antisymmetric state dark). This is the same operator Cattaneo 2005.06229 (Eq. 4 + symmetric limit)
specializes to SC transmons and McDermott 2201.11193 (Eq. 43–46) writes in MCWF-ready diagonal form.

**Magnitude:** `gamma_12 in [0, gamma]` — Eq. (48) bounds `|gamma_12| <= gamma` (= at `k r_12 -> 0`).
The fraction `eta = gamma_12 / gamma in [0,1]` is the cooperativity; for the QEC-Twin's
*incidental* shared bath this is **swept (class (c))** — the free-space dipole formula (Eq. 48) is
geometry-specific (atoms in vacuum at separation `r_12`) and does not transfer a hardware
`gamma_12` value to a transmon QEC chip; it transfers the OPERATOR FORM and the bound.

---

## The OBSERVABLE / metric [paper]

NOT the M12 observable — this review's observables are entanglement measures (concurrence,
negativity) and the super/sub-radiant decay-rate split. M12's process-infidelity `1 - F_e` is
grounded in `schumacher_nielsen_entanglement_fidelity_quant-ph-0205035.md`. This paper is an
OPERATOR anchor. (It does confirm the *structural* signature: subradiance = the antisymmetric
`(sigma^-_1 - sigma^-_2)` mode at rate `gamma - gamma_12 -> 0` — the dark mode that proves the jump
is genuinely collective, not two independent T1.)

---

## Findings + numbers [paper]

- **Eq. 47 (Lehmberg–Agarwal master equation)** — the canonical collective two-atom decay
  generator; (a)-class standard form.
- **`gamma_ii = gamma` (Einstein A), `gamma_ij` (`i!=j`) = collective damping (Eq. 48)**;
  **`gamma_12 -> gamma` as `k r_12 -> 0`** (Eq. 50).
- **Symmetric rate `gamma + gamma_12`, antisymmetric rate `gamma - gamma_12`** (Eq. 53);
  superradiant `-> 2 gamma`, subradiant `-> 0` at small separation.
- No device numbers (free-space atomic-physics review).

---

## Limitations [paper]

- **Free-space atoms, not superconducting qubits.** The collective coefficients (Eq. 48) are the
  free-space dipole–dipole geometry (`k r_ij` separation, dipole orientation `mu_hat`). The operator
  FORM is universal (any two emitters sharing a bath), but the *magnitude* `gamma_12(k r_12)` is
  geometry-specific to vacuum-coupled atoms — for SC qubits use Cattaneo Eq. (A1)
  (`gamma_12 ~ g1 g2 J(omega)`) instead. [So this paper is DIRECT for the OPERATOR, not for a
  hardware magnitude.]
- **Born–Markov, weak-coupling, zero-temperature** (Eq. 47 stated at T=0; thermal `sigma^+` channels
  added in the SC-qubit version).
- **Review, not new derivation** — Eq. 47 originates Lehmberg 1970 / Agarwal 1974 [refs 21,22]; this
  is the standard reference that writes them down cleanly.

---

## Relevance to qec_twin M12 [ours]

1. **DIRECT operator anchor (textbook-grade).** Eq. (47) is THE explicit collective Lindblad master
   equation M12 lowers; Eq. (53) gives the super/subradiant rate split `gamma +/- gamma_12` that is
   the defining signature of the collective jump. Together with Cattaneo 2005.06229 (the SC-qubit
   specialization) this gives **two DIRECT explicit-Lindblad operator anchors**, closing the gap
   Ojanen/Mlynek's notes flagged ("needs a standard Lindblad-Dicke reference").
2. **Bounds the magnitude:** `|gamma_12| <= gamma` (Eq. 48 maximum at `k r_12 -> 0`) ⇒ `eta =
   gamma_12/gamma in [0,1]`. Consistent with Mlynek's measured `eta ~ 1` (engineered) and the
   bracketed incidental fraction (class (c)).
3. **Diagonalization to collective jumps** (symmetric/antisymmetric) is the MCWF-implementation
   bridge — same as McDermott 2201.11193.
4. **Confirms non-additivity:** the off-diagonal `gamma_12` in the PSD `gamma` matrix is why M12 is
   not `T1_a (x) T1_b` (jaschke 1804.09796).

---

## How to use / trust + open questions [ours]

- **Trust:** very high for the operator form (Eq. 47/53 are the field-standard collective-decay
  master equation, cross-checked against Breuer–Petruccione §3.4 and the Cattaneo SC-qubit Eq. 4).
  The greek-glyph mangling was resolved by reading via a utf-8 python reader + transcribing against
  the known standard form; the `(gamma + gamma_12)` / `(gamma - gamma_12)` rate split (Eq. 53) and
  the `gamma_12 -> gamma` small-separation limit (Eq. 50) are read verbatim.
- **Convention to carry:** Eq. (47) writes the dissipator with the `({rho S^+_i, S^-_j} + {S^+_i,
  S^-_j rho})` form (Lehmberg convention); the standard GKSL form is the same up to the
  bookkeeping shown above. The symmetric collective jump is `(sigma^-_1 + sigma^-_2)/sqrt(2)` with
  rate `gamma + gamma_12` (NOT `sqrt(2)`-absorbed); carry the normalization with the number.
- **Open question:** none for the operator form. The hardware `gamma_12` magnitude does NOT come
  from this paper (free-space geometry) — it is swept (class (c)), bounded by `eta <= 1`.
