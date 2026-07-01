# Full-text 精读 — Ojanen et al., "Global relaxation in superconducting qubits" (arXiv:0705.1085)

> **Provenance (2026-06-30): FULL-TEXT 精读.** Source:
> `outputs/papers/0705.1085.txt` (PyMuPDF text extraction, 4 pages, ~20 k chars).
> Figures are not pixel-extracted; all equation and section references are from the
> extracted text. Published version: arXiv:0705.1085v3 [cond-mat.mes-hall], 3 Oct 2007.
> (No journal citation line in the extracted text; accepted venue not identified from
> this extract.)

Epistemic tags throughout: **[paper]** = stated/derived in the paper;
**[twin]** = our application or inference.

---

## Why load-bearing [twin]

This note is the primary literature anchor for QEC-Twin **M12 =
correlated two-qubit relaxation** (collective / Dicke jump). M12 models two
superconducting qubits sharing a common bath so that a collective Lindblad jump
operator `L = sqrt(gamma_corr) * (sigma1^- + sigma2^-)` causes correlated amplitude
damping. Ojanen et al. is the **only paper in the reading-notes corpus that (a)
studies exactly this scenario — two superconducting qubits under a *global* common
bath — and (b) derives the super/subradiant rate splitting** that is the physical
hallmark of the collective jump. It is therefore the load-bearing physics reference
for (1) the operator form justification and (2) the rate structure.

---

## Metadata [paper]

- **Authors:** T. Ojanen (Helsinki Univ. of Technology), A. O. Niskanen (VTT /
  CREST-JST), Y. Nakamura (NEC / RIKEN / CREST-JST), A. A. Abdumalikov Jr. (RIKEN /
  Physical-Technical Inst. Tashkent).
- **arXiv:** 0705.1085v3, cond-mat.mes-hall, 3 Oct 2007.
- **Type:** theoretical proposal + numerical example (no measurements reported in this
  paper).
- **Subject:** Two interacting flux qubits coupled to a single common bath; Dicke
  super/subradiance adapted to superconducting circuits; proposed experimental
  verification using a cavity-coupled pair of flux qubits.

---

## Executive summary [paper]

Two qubits sharing a **global** quantum bath (long-wavelength environmental
fluctuations, equal coupling strengths) exhibit Dicke-type correlated relaxation: the
symmetric (superradiant) state `|phi_s> = (|+-> + |-+>)/sqrt(2)` decays **faster**
than a single-qubit excitation, while the antisymmetric (subradiant) state
`|phi_a> = (|+-> - |-+>)/sqrt(2)` is **exactly stable** (zero decay rate) under
perfectly matched couplings. When qubit-bath coupling constants differ slightly
(`g1 != g2`) or qubit energies are slightly detuned (`Delta1 != Delta2`), the
subradiant state acquires a small but nonzero decay rate quadratic in the mismatch.
The paper derives these rates analytically using Golden-Rule perturbation theory,
provides a numerical example with realistic flux-qubit parameters, and proposes a
dispersive-readout flux-qubit experiment to measure the two dramatically different
relaxation times.

---

## The model and master equation [paper]

**System Hamiltonian (Eq. 1 of the paper):**

```
H = H_q + H_env + H_i

H_q = -(Delta/2) * sum_i sigma^(i)_z  +  J * sum_{i<j} sigma^(i)_x sigma^(j)_x

H_i = g * x_hat * sum_i sigma^(i)_x
```

Here `x_hat` is a Hermitian bath operator, `Delta` is the common qubit energy
splitting, `J` is the qubit-qubit interaction, and `g` is the common qubit-bath
coupling constant. **[paper]** The assumption of equal `Delta`, `J`, and `g` for both
qubits realises the **global bath** (Dicke) condition.

**Note on Lindblad form:** **[paper]** The paper does NOT write the master equation in
explicit Lindblad form with jump operators. It works directly in the energy eigenstate
basis and extracts transition rates via Golden-Rule (perturbation theory) from the
propagator `G(ij, t; kl, t0) = Tr_env[rho_env <l,t0| T~ e^{...} |j,t> x <i,t| T
e^{...} |k,t0>]` (Eq. 2). The emergent physics is Dicke super/subradiance, which is
equivalent to what the Lindblad equation with a collective jump operator produces, but
the paper derives rates, not the jump-operator form.

**[twin]** The equivalence between the rate structure derived here and the Lindblad
equation with a collective jump `L = sqrt(Gamma_0) * (sigma1^- + sigma2^-)` is
standard: in the Born-Markov-secular (Redfield) derivation of the Dicke master
equation, the two-qubit Lindblad dissipator with that collective operator yields
`Gamma_phi_s = 2*Gamma_0` (superradiant) and `Gamma_phi_a = 0` (subradiant, exactly
dark), exactly matching Ojanen et al.'s results. The operator form `L = sqrt(gamma_corr)
* (sigma1^- + sigma2^-)` is the standard Dicke-model Lindblad representation; Ojanen
et al. ground the rates, not the operator notation.

---

## The correlated-rate magnitude and structure [paper]

This is the load-bearing extraction for M12.

### Single-qubit baseline rate (Eq. 3)

```
Gamma_{2->1} = Gamma_{3->1} = (g^2 / hbar^2) * S_x(Delta/hbar)
```

where `S_x(omega) = integral_{-inf}^{inf} <x_hat(t) x_hat(0)> e^{i omega t} dt` is
the bath noise power spectral density at the qubit frequency. **[paper]** This is the
ordinary single-qubit Golden-Rule relaxation rate; both `|2> = |-->+>` and
`|3> = |+>->` decay at this rate. **[paper]** The paper notes explicitly: "The factor
`g^2/hbar^2 * S_x(omega)` appearing in the above formulas is the characteristic
relaxation rate for individual qubits."

### Superradiant (symmetric) rate — J = 0 case

**[paper]** `Gamma_{phi_s -> 1} = 2 * Gamma_{2->1}` (twice the single-qubit rate).

### Subradiant (antisymmetric) rate — J = 0 case, equal couplings

**[paper]** `Gamma_{phi_a -> 1} = 0` (exactly zero, non-perturbative result, not
relying on perturbation theory).

### Symmetric/antisymmetric rates with inter-qubit coupling J != 0 (Eq. 4)

```
Gamma_{phi_s -> d} = (g^2/hbar^2) * 2*(a+b)^2 * S_x( (sqrt(Delta^2 + J^2) + J) / hbar )
```

`|phi_a>` **remains exactly stable** (`Gamma_{phi_a} = 0`) even for `J != 0`.

### Effect of unequal bath couplings g1 != g2 (Eq. 5)

```
Gamma_{phi_j -> d} = ((g1 +/- g2)^2 / (2 * hbar^2)) * (a+b)^2 * S_x( (sqrt(Delta^2+J^2) +/- J) / hbar )
```

upper signs for `j = s`, lower for `j = a`. **[paper]** The ratio:

```
Gamma_{phi_s -> 1} / Gamma_{phi_a -> 1} = (g1 + g2)^2 / (g1 - g2)^2
```

which is very large when `g1 ≈ g2`, "clearly demonstrating a dramatic difference."
**[paper]** The subradiant decay vanishes as the **square of the coupling detuning**
`(g1 - g2)^2`.

### Numerical example with realistic flux-qubit parameters (Eqs. 10-11)

**[paper]** With `(Delta2 - Delta1)/h = 200 MHz`, `Delta1/h = 6 GHz`,
`J/h = 1 GHz`, `epsilon1/h = 200 MHz`, `epsilon2 = 0`:

```
Gamma_{phi_s -> d} = 1.7 * (g^2/hbar^2) * S_x(2 pi * 7.2 GHz)       (Eq. 10)
Gamma_{phi_a -> d} = 4.0e-3 * (g^2/hbar^2) * S_x(2 pi * 5.2 GHz)    (Eq. 11)
```

**[paper]** "Assuming that the noise spectrum `S_x(omega)` does not have too strong
frequency dependence we then expect **two orders of magnitude different relaxation
times** for the sub- and superradiant states even with very typical parameters."
**[paper]** "The factor `g^2/hbar^2 * S_x(omega)`... is the characteristic relaxation
rate for individual qubits. This could be typically, say, **1 µs**. This translates
into a **250 µs lifetime of the antisymmetric state** under global noise while the
**symmetric state decays in about 0.6 µs**."

### Is there a quantitative correlated-rate value?

**[paper]** The paper does NOT report a measured correlated rate from a real device.
The paper is a **theoretical proposal**; the experiment it designs had not yet been
performed. The numerical example (Eqs. 10-11) uses estimated parameters, not
measurement data. The only device-level number given is the single-qubit coherence
estimate "typically, say, 1 µs" — used to illustrate the ratio, not a measured value
for the correlated component.

**[twin] VERDICT: NO quantitative measured value for the correlated relaxation rate
(gamma_corr) in any real superconducting device is provided by this paper. The
correlated rate must be BRACKETED (declared as a swept, unsourced range) if used in
M12 simulations.**

---

## Regime for strong correlation [paper]

**[paper]** The conditions stated or implied for strong global-bath correlation
effects are:

1. **Frequency degeneracy:** `Delta1 ≈ Delta2` — the qubit energy splittings must be
   matched. The subradiant protection degrades as `|Delta_a|/J` grows (Eq. 8
   regime). The example uses `(Delta2 - Delta1)/h = 200 MHz` vs `J/h = 1 GHz`, i.e.,
   `|Delta_a|/J ≈ 0.1`, which already gives only two orders of magnitude separation,
   not perfect subradiance.

2. **Proximity / common bath (long-wavelength limit):** "qubits are coupled to the
   same quantum bath with approximately equal strengths, appropriate for
   **long-wavelength environmental fluctuations**." The condition is that the
   environmental correlation length is much larger than the inter-qubit distance,
   i.e., the fluctuation wavelength `lambda_env >> d_12` (inter-qubit separation).
   The paper does not quantify a specific proximity bound.

3. **Matched bath coupling strengths:** `g1 ≈ g2`. The subradiant protection
   `Gamma_{phi_a} ∝ (g1-g2)^2` is zero only when couplings are equal; any asymmetry
   lifts the dark state.

4. **Large inter-qubit coupling J (protection from parameter scatter):** A large `J`
   protects the eigenstates from parameter fluctuations (`|Delta_a|/J << 1` regime)
   and maintains the super/subradiant structure under imperfections.

---

## Relevance to qec_twin M12 [twin]

### (a) Does this paper support the collective Dicke operator form for superconducting qubits?

**YES — indirectly, with a caveat.** The paper derives, for superconducting flux
qubits under a global bath, the exact rate structure (`Gamma_s = 2*Gamma_0`,
`Gamma_a = 0` for equal couplings) that is the defining signature of a Lindblad
master equation with collective jump operator `L = sqrt(Gamma_0)*(sigma1^- + sigma2^-)`.
The Hamiltonian (Eq. 1) and Dicke-model physics are exactly the setup for which the
standard Lindblad Dicke master equation applies. **[twin]** The Lindblad form with
collective jump `L = sqrt(gamma_corr)*(sigma1^- + sigma2^-)` (or equivalently
`L_pm = sqrt(Gamma_±)*(sigma1^- ± sigma2^-)` for the two collective modes) is the
standard dissipator representation of this physics (see e.g. the Dicke-model Lindblad
literature: Agarwal 1974, Lehmberg 1970). **However, the paper itself never writes
the Lindblad equation or the jump operator explicitly.** The operator form is
supported by the physical model (common bath, σx coupling, equal strengths) and the
rate results, not by an explicit Lindblad statement in this paper. Certificate-grade
for the operator form requires supplementing this paper with a standard reference that
explicitly derives the Lindblad Dicke master equation (e.g., Agarwal 1974 or Gardiner
& Zoller).

### (b) Does this paper provide a quantitative anchor for gamma_corr ≈ 0.01-0.1*gamma_1?

**NO. No quantitative correlated-rate value or range is pinned.** The paper provides:
- The **rate ratio** `Gamma_s / Gamma_single = 2` (exact, for equal couplings) and
  `Gamma_a / Gamma_single = 0` — these are structural, not magnitude bounds.
- The **numerical prefactors** 1.7 and 4.0×10⁻³ (Eqs. 10-11) for the symmetric and
  asymmetric states relative to `(g^2/hbar^2)*S_x(omega)`, under specific estimated
  device parameters — not a measurement.
- A **single-qubit lifetime estimate of "typically, say, 1 µs"** — a rough order-of-
  magnitude reference used to calibrate the 250 µs / 0.6 µs prediction, not a
  measured correlated-rate value.

**[twin]** The quantity `gamma_corr` as used in M12 (the off-diagonal cross-
relaxation rate in the Lindblad equation, sometimes written as `Gamma_12` or
`Gamma_cross` in standard dissipation theory) corresponds to `Gamma_0` in the
Dicke limit where `Gamma_s = 2*Gamma_0` and `Gamma_a = 0`. This paper confirms
that in the ideal global-bath limit, `gamma_corr = gamma_1` (fully correlated:
`Gamma_cross = Gamma_single`). But **no measurement of how close real devices come to
this limit is provided**. Whether actual hardware has `gamma_corr` at 10%, 50%, or
100% of `gamma_1` is not answered here.

**CONCLUSION: gamma_corr must be BRACKETED as a swept range in M12 simulations.
This paper does NOT pin a magnitude. Appropriate range to declare: 0 (independent
baths) to gamma_1 (perfect global bath), with no empirical anchor for the physically
realized fraction in current superconducting hardware.**

---

## Limitations [paper]

1. **Theoretical proposal; no experimental data.** All numbers are estimates from
   assumed device parameters; the predicted 250 µs / 0.6 µs lifetime split had not
   been measured at the time of publication.
2. **Golden-Rule (weak-coupling) perturbation theory.** The transition rates are
   derived to lowest non-vanishing order in `g`; strong-coupling corrections are not
   computed.
3. **Markov approximation** is implicit (correlation functions enter only through the
   spectral density `S_x(omega)` at specific frequencies, i.e., the Born-Markov
   limit).
4. **Equal-energy-splitting simplification as baseline.** The primary analytic results
   assume `Delta1 = Delta2`, `g1 = g2`; the detuned case introduces additional
   structure (Eqs. 5-8) but the regime validity `|Delta_a|/J << 1` is required for
   Eq. 8's simplification.
5. **No Lindblad-form master equation given.** The paper operates at the rate level,
   not the density-matrix equation level; the explicit jump-operator Lindblad form
   must be inferred from standard open-quantum-systems theory.
6. **Flux qubit specific.** The `sigma_x ⊗ sigma_x` bath coupling form applies to
   "optimally biased superconducting qubits" (flux qubits at the half-flux quantum
   point). Transmons or charge qubits near their optimal points have different coupling
   geometry; the qualitative physics transfers but the coupling form differs.
7. **No multi-qubit (> 2 qubit) generalization.** The analysis is two-qubit-exact;
   scaling to N qubits in a QEC patch is not addressed.

---

## Trust [twin]

- **Operator form (Dicke / collective jump):** numerics-grade for this paper alone
  (the rate structure is certificate-grade, the explicit Lindblad form must be sourced
  elsewhere). Combine with a standard Lindblad-Dicke reference for certificate-grade.
- **Rate structure (Gamma_s = 2*Gamma_0, Gamma_a = 0):** certificate-grade — this
  follows non-perturbatively from the symmetry argument for `Gamma_a` and from
  Golden-Rule for `Gamma_s`; the paper notes the former "does not rely on perturbation
  theory."
- **Numerical prefactors (Eqs. 10-11):** numerics-grade (specific device parameters,
  no experimental validation at time of publication).
- **Magnitude of gamma_corr in real devices:** ABSENT — no number; must be bracketed.
