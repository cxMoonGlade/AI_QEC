# Full-text 精读 — Cattaneo, Giorgi, Maniscalco, Paraoanu, Zambrini, "Bath-induced collective phenomena on superconducting qubits: synchronization, subradiance, and entanglement generation" (arXiv:2005.06229; Phys. Rev. A 103, 062217 (2021))

> **Provenance (2026-06-30): FULL-TEXT 精读.** PDF `outputs/papers/2005.06229.pdf` → txt
> `outputs/papers/2005.06229.txt` (PyMuPDF, 22 pages, ~130k chars). All §/Eq/Fig refs read
> verbatim from that text. Greek/math glyphs are mangled by the extractor (e.g. `γ↓`, `σ−`);
> equations transcribed by hand from the mangled text against the standard collective-decay
> master-equation literature. Figures not pixel-extracted (figure facts = captions + in-text
> numbers).

---

## Why this note is load-bearing [ours]

**M12 = correlated two-qubit relaxation** in the QEC-Twin is the same-substep **two-site
joint collapse operator** `L = sqrt(gamma_corr) (sigma1^- + sigma2^-)` that relaxes two
qubits through a shared bath. The two prior SC-qubit anchors (Ojanen 0705.1085, Mlynek
1412.2392) both ground the **rate structure** (`Gamma_s = 2 Gamma_0`, `Gamma_a = 0`) but
**neither writes the explicit Lindblad jump operator** — both notes flag that "certificate-grade
for the operator form requires supplementing with a standard reference that explicitly derives
the Lindblad Dicke master equation." **This paper is that reference for the superconducting-qubit
setting:** it writes the explicit collective-dissipation Lindblad master equation (Eq. 2/4) with
the cross-relaxation coefficient matrix `gamma_jk` (Eq. A1) for **two transmon qubits in a common
bath**, and states the fully symmetric limit `gamma = gamma_jk` for all `j,k` (the M12 operator).
It is the DIRECT, explicit-Lindblad, on-platform (transmon) operator anchor M12 was missing.

---

## Metadata [paper]

- **Authors:** Marco Cattaneo (IFISC CSIC-UIB + Univ. Helsinki), Gian Luca Giorgi (IFISC),
  Sabrina Maniscalco (Helsinki + Aalto), Gheorghe Sorin Paraoanu (Aalto), Roberta Zambrini (IFISC).
- **arXiv:** 2005.06229v? [quant-ph], dated 5 May 2021.
- **Published:** Phys. Rev. A **103**, 062217 (2021); also Ann. Phys. (Berlin) version listed.
- **Type:** theory + numerics (open-system master equation) + a proposed experimental
  implementation (two transmons capacitively coupled to a common resistor).
- **System:** two superconducting transmon qubits dissipating into a COMMON bath (Ohmic, the
  Johnson–Nyquist spectrum of a shared resistor); the qubits are NOT directly coupled, so all
  cross-correlations are bath-induced.

---

## Executive summary [paper]

A common environment on two qubits produces collective phenomena — bath-induced entanglement,
quantum synchronization, subradiance. The dynamics obey a Born–Markov **partial-secular**
Lindblad master equation (Eq. 2) whose dissipator (Eq. 4) carries off-diagonal cross-damping
coefficients `gamma_jk` (`j != k`) from the common bath. The paper maps the parameter regimes
(coupling weights `g1, g2`, detuning `Delta omega = omega1 - omega2`, temperature `T`,
local `T1`) where each collective effect appears, and proposes two transmons + a common resistor
as the experimental platform. The load-bearing fact for M12: the cross-relaxation coefficient
`gamma_12 = g1 g2 (Gamma_beta(omega1) + Gamma_beta(omega2)^*)` (Eq. A1) is **nonzero only via the
common bath** (the `g1 g2` product), and in the symmetric limit `g1=g2, Delta omega=0` collapses
to a single rate `gamma = gamma_jk` for all `j,k` — exactly the collective Dicke jump.

---

## Method (deep) [paper]

### System + bath Hamiltonian (Eq. 1)

```
H = H_S + sum_k hbar Omega_k b_k^dagger b_k + mu sum_k (g1 sigma^x_1 + g2 sigma^x_2) f_k (b_k + b_k^dagger)
H_S = (hbar omega1 / 2) sigma^z_1 + (hbar omega2 / 2) sigma^z_2          [eigvecs |gg>,|ge>,|eg>,|ee>]
```

- `|e>, |g>` = excited / ground; `omega1, omega2` = qubit frequencies.
- `g1, g2` = **dimensionless weights of the dissipative coupling** of each qubit to the common bath.
- `mu` = coupling constant (energy units); `{f_k}` set the bath spectral density (taken Ohmic,
  justified for a common resistor → Johnson–Nyquist).
- **The qubits are NOT directly interacting** — deliberately, so the collective effects are
  unambiguously bath-induced.

### The master equation (Eq. 2, partial secular)

```
d rho_S / dt = L[rho_S] = -(i/hbar) [H_S + H_LS, rho_S] + D[rho_S]                  (2)
```

**Lamb-shift Hamiltonian (Eq. 3):**
```
H_LS = sum_{j,k=1,2} hbar ( s^down_jk sigma^+_k sigma^-_j  +  s^up_jk sigma^-_k sigma^+_j )      (3)
```

**Dissipator (Eq. 4) — THE LOAD-BEARING EQUATION:**
```
D[rho_S] = sum_{j,k=1,2} gamma^down_jk ( sigma^-_j rho_S sigma^+_k - (1/2){rho_S, sigma^+_k sigma^-_j} )
         + sum_{j,k=1,2} gamma^up_jk   ( sigma^+_j rho_S sigma^-_k - (1/2){rho_S, sigma^-_k sigma^+_j} )   (4)
```

- `gamma^down_jk` = the **relaxation** (downward, `sigma^-`) coefficient matrix; the **diagonal**
  `gamma^down_11, gamma^down_22` are the single-qubit T1 rates, the **off-diagonal**
  `gamma^down_12 = gamma^down_21^*` is the **correlated / cross relaxation rate** (M12's `gamma_corr`).
- `gamma^up_jk` = the thermal-excitation (upward, `sigma^+`) coefficient matrix (= 0 at T=0).
- Validity: weak coupling `omega1, omega2 >> mu/hbar` + Markovian (Ohmic) bath. **Partial** secular
  (keeps the slowly-rotating `omega1 - omega2` cross terms) so it works at small detuning where the
  full-secular equation fails.

### Coefficient matrix (Appendix A, Eq. A1) — THE EXPLICIT CROSS-RATE

```
gamma^down_jk = g_j g_k ( Gamma_beta(omega_j) + Gamma_beta(omega_k)^* )  +  (1/T1) delta_jk         (A1)
gamma^up_jk   = g_j g_k ( Gamma_beta(-omega_j) + Gamma_beta(-omega_k)^* )
s^down_jk     = g_j g_k ( Gamma_beta(omega_j)  - Gamma_beta(omega_k)^* ) / (2i)
s^up_jk       = g_j g_k ( Gamma_beta(-omega_j) - Gamma_beta(-omega_k)^* ) / (2i)
```
with `Gamma_beta(omega) = pi (N_beta(omega) + 1) J(omega) + i (principal-value shift)` (Eq. A2),
`N_beta(omega) = 1/(e^{beta hbar omega} - 1)` the Bose occupation, `J(omega)` the Ohmic spectral
density (Eq. A3/A4). **The off-diagonal `gamma^down_12` is proportional to `g1 g2`** — it exists
ONLY because both qubits couple to the SAME bath. Add the phenomenological local bath `1/T1` only
on the diagonal (`delta_jk`).

### The symmetric (M12) limit (paper §V.A.2, "T -> infinity", line ~592)

> [paper] "exact analytical results can be derived for `g1 = g2`, `Delta omega = 0`, so that there
> is a **single dissipative coefficient `gamma = gamma^down_jk = gamma^up_jk`**." In this limit the
> **antisymmetric (subradiant) state lives in a decoherence-free subspace**, `lambda^(0)_5 = 0`,
> "and it never decays, independently of the chosen temperature."

This is the M12 operator: `gamma^down_11 = gamma^down_22 = gamma^down_12 = gamma`, for which the
dissipator (Eq. 4) is exactly the collective Dicke dissipator with jump operator
`L = sqrt(gamma) (sigma^-_1 + sigma^-_2)` (acting only on the symmetric subspace; the antisymmetric
state is dark). See "the operator algebra" below.

### Number-conservation / secular block structure (paper §, Appendix B)

The partial-secular Liouvillian is **phase-covariant**: `L` commutes with the
excitation-number superoperator `N = [N, .]`, so it block-diagonalizes into 5 blocks indexed by
`d = -2..2` (the change in total excitation number), of dimension `1, 4, 6, 4, 1` (Eq. ~line 184).
[ours] This is exactly the excitation-grading the Axis-1 carrier preserves; the M12 collapse moves
weight DOWN one excitation block (`d = -1`), like single-qubit T1 but jointly.

---

## The collective-jump operator algebra (Eq. 4 in the symmetric limit) [paper → ours]

[ours, derived from the paper's Eq. 4 + symmetric-limit statement] Define the symmetric and
antisymmetric collective lowering operators
```
S^-_sym  = (sigma^-_1 + sigma^-_2) / sqrt(2)
S^-_anti = (sigma^-_1 - sigma^-_2) / sqrt(2)
```
For `gamma^down_11 = gamma^down_22 = gamma^down_12 = gamma`, the relaxation part of Eq. (4)
diagonalizes:
```
D_relax[rho] = Gamma_sym  ( S^-_sym  rho S^+_sym  - (1/2){rho, S^+_sym  S^-_sym } )
             + Gamma_anti ( S^-_anti rho S^+_anti - (1/2){rho, S^+_anti S^-_anti} )
with  Gamma_sym = gamma + gamma_12 = 2 gamma,   Gamma_anti = gamma - gamma_12 = 0.
```
So the ONLY surviving collapse channel is the **symmetric collective jump**
`C_sym = sqrt(2 gamma) S^-_sym = sqrt(gamma) (sigma^-_1 + sigma^-_2)` — exactly M12's
`L = sqrt(gamma_corr) (sigma^-_1 + sigma^-_2)`. The antisymmetric channel is dark (`Gamma_anti = 0`).
This matches Ojanen (`Gamma_s = 2 Gamma_0`, `Gamma_a = 0`) and Mlynek (`Gamma_bright = 2 Gamma_kappa`,
`Gamma_dark = 0`) and is the unitary-of-the-jump-operators / diagonalize-`gamma` statement made
explicit in McDermott 2201.11193 Eq. (43)–(46).

**This note GROUNDS the explicit Lindblad operator form for superconducting (transmon) qubits**,
which Ojanen and Mlynek individually did not write out. The cross-rate `gamma_12 = g1 g2 (...)`
(Eq. A1) makes precise *why* the joint collapse cannot be split into two independent T1 channels
(the cross term is a genuine off-diagonal of the PSD `gamma` matrix).

---

## The OBSERVABLE / metric [paper]

This paper's figures of merit (subradiance measure, negativity for entanglement,
"collectiveness" `bar I_M`, synchronization) are **NOT** the M12 observable — they are
steady-state/long-time collective witnesses, not the same-substep `1 - F_e`. M12's observable
(process infidelity `1 - F_e` of the substep channel vs the independent oracle) is grounded
separately in `schumacher_nielsen_entanglement_fidelity_quant-ph-0205035.md`. This paper is an
OPERATOR anchor only. (It does, however, confirm the right *structural* signatures: subradiance =
the dark `(sigma^-_1 - sigma^-_2)` mode never decaying, the hallmark that distinguishes a genuine
collective jump from independent T1.)

---

## Findings + numbers [paper]

- **Dissipator with cross-damping (Eq. 4)** and **explicit coefficient matrix (Eq. A1)** — the
  load-bearing results; exact (a)-class identities given the Born–Markov–partial-secular derivation.
- **Symmetric limit (`g1=g2`, `Delta omega=0`): single coefficient `gamma = gamma_jk`**, subradiant
  state in a decoherence-free subspace (`lambda^(0)_5 = 0`, never decays). (line ~592–598.)
- **Vanishing-collectiveness limits:** `bar I_M = 0` for (i) `mu^2 << 1/T1` (local dissipation
  dominates), (ii) `g2 -> 2, g1 -> 0` (bath hits only one qubit), (iii) `Delta omega = O(omega1)`
  (full secular applies). (line ~585–588.) → [ours] these are exactly the `gamma_12 -> 0` (M12
  reduces to two independent T1) regimes.
- **Experimental parameters (proposed):** `mu = 10^-2 hbar omega1`, `beta = 10 / hbar omega1`,
  `T1 = 3 x 10^5 / omega1`, Ohmic `J(omega)` (Eq. A4). (line ~909.) [ours] illustrative, not
  a measured `gamma_12` value.

---

## Limitations [paper]

- **No measured `gamma_12` on a real device.** This is a theory+proposal paper; the transmon +
  common-resistor implementation is proposed, not built here. The magnitude of `gamma_12` is set by
  `g1 g2` and the resistor's Ohmic spectrum — a design parameter, not a characterized hardware number.
- **Two qubits only**; multi-qubit generalization "deserves a separate study" (line ~1242).
- **Born–Markov + (partial) secular + weak coupling** (`omega >> mu/hbar`). Strong-coupling /
  non-Markovian corrections not treated.
- **Engineered common bath** (a shared resistor by design) — like Mlynek, this is the
  *cooperative-by-construction* regime, not the incidental/parasitic shared bath M12 nominally
  targets; the operator FORM transfers, the incidental magnitude does not.

---

## Relevance to qec_twin M12 [ours]

1. **This is the explicit-Lindblad operator anchor for SC qubits that closes the M12 operator
   gap.** Ojanen + Mlynek gave the rate structure; THIS paper writes the dissipator (Eq. 4) and the
   cross-rate matrix (Eq. A1) and states the symmetric-limit single-`gamma` collapse — the exact
   `L = sqrt(gamma_corr)(sigma^-_1 + sigma^-_2)` M12 implements. Classify **DIRECT** for the operator.
2. **The cross-rate is `g1 g2`-weighted (Eq. A1)** — grounds that the off-diagonal `gamma_12` is a
   *genuine* collective coefficient (common-bath only), so M12's joint collapse is NOT
   `T1_a (x) T1_b` (two independent channels) — consistent with the jaschke 1804.09796 non-additivity
   result (`L = A+B` cannot be split without dropping cross terms).
3. **MCWF representation:** to put Eq. (4) on the MCWF carrier the off-diagonal `gamma` matrix must
   be **diagonalized into collective jump operators** before sampling jumps — this is the
   McDermott 2201.11193 Eq. (43)–(46) procedure (`U^-_s, U^-_a`), the implementation seam for the
   2-site collapse path in `axis1_mcwf_mps_execution.py`.
4. **Magnitude stays bracketed (class (c)).** This paper, like Ojanen/Mlynek, does not pin the
   incidental `gamma_12 / gamma_1` fraction for a real QEC processor — `eta = gamma_12/gamma_1 in
   [0,1]`, swept. The physical bound `eta <= 1` (= the symmetric single-`gamma` limit here, and
   Mlynek's 2x) holds.

---

## How to use / trust + open questions [ours]

- **Trust:** very high for the operator form. Full-text 精读; Eq. (4) + Eq. (A1) + the symmetric-limit
  statement are transcribed directly. The dissipator (Eq. 4) is the field-standard collective-decay
  Lindblad form for two SC qubits (consistent with Breuer–Petruccione / the Lehmberg–Agarwal form in
  Ficek 1002.4124 Eq. 47). Greek glyph mangling in the extractor was cross-checked against the
  standard form; the structure (`sigma^-_j rho sigma^+_k - (1/2){rho, sigma^+_k sigma^-_j}`) is
  unambiguous.
- **Convention to carry:** this paper's `gamma_12` is the off-diagonal of the `sigma^-`
  PSD coefficient matrix; in the symmetric limit `gamma_11 = gamma_22 = gamma_12 = gamma` ⇒
  `Gamma_sym = 2 gamma`, `Gamma_anti = 0`. (McDermott uses a `1/2` prefactor convention,
  `Gamma_s = (1/2)(Gamma + Gamma_12)`; same physics, different dissipator normalization — carry the
  convention with the number.)
- **Open question (implementation):** the M12 carrier seam should build the **diagonalized**
  collective jumps (`sqrt(2 gamma) S^-_sym` for the fully cooperative case, or the eigen-jumps of the
  general `gamma` matrix), then certify the substep channel `1 - F_e` against the independent oracle
  `assemble_substep_channel` built from the same Eq. (4) dissipator (the oracle takes the full
  `c_list`, so it does not need the diagonalization — the cert checks the carrier's diagonalized
  collapse reproduces the oracle's dense Liouvillian to `<= 1e-1` GROSS + `O(1/m^2)` convergence).
