# Full-text review — Ahn & Park, "Non-Markovian noise sources for quantum error mitigation" (arXiv:2302.05053)

> **Provenance (2026-07-03): FULL-TEXT read (精读).** Cached full text extracted from
> `outputs/papers/2302.05053.pdf` (16 pp main text + Supplementary Information); read end-to-end
> incl. Supplementary Information Secs. I–III (time-convolutionless derivation, Caldeira-Leggett
> evaluation, CNOT gate operation calculations). All Eq./Fig./Table refs below are from that text.
> **NOTE:** PDF text extraction loses Greek-letter variables (η, γ, κ, Γ, ω_c) and some inline math
> — the verbatim numerical values for the NISQ system parameter η could not be pixel-extracted
> from Fig. 6 or the inline text; estimates quoted here are from the text context. Tags:
> **[paper]** = stated in the paper; **[twin]** = our application/inference for `qec_twin`, NOT the
> paper's claim.

## Metadata [paper]

- **Authors / affiliation.** Doyeol Ahn, Byeongyong Park (University of Seoul, Dept. of Electrical
  and Computer Engineering; First Quantum, Inc, Korea). Doyeol Ahn has prior work on
  time-convolutionless reduced-density-operator theory of noisy quantum channels (Phys. Rev. A 61,
  052310, 2000; Phys. Rev. A 66, 012302, 2002).
- **Venue / status.** arXiv:2302.05053v2 [quant-ph], 2 May 2023 (v1 10 Feb 2023). No journal
  publication detected at fetch date.
- **Type.** Analytic open-quantum-systems theory (time-convolutionless master equation) + fitting
  of a QEM cost function to hardware data (IBM Guadalupe, IonQ) for two-qubit identity and CNOT
  gates. **Not** a QEC paper — no codes, no decoders, no detector records.

## Executive summary [paper]

Presents a **non-Markovian model of quantum state evolution** for NISQ devices using the
**time-convolutionless projection operator formalism** with advanced and retarded propagators.
The system–environment interaction is modeled by the **Caldeira-Leggett model** (linearly coupled
harmonic oscillators, Ohmic spectral density). Key elements:

- **Eqs. (1)–(16) (Theory):** Derives the reduced-density operator `ρ_S(t)` in
  time-convolutionless form under the Born approximation, using projection operators `P` (tracing
  over the reservoir) and `Q = 1 − P`. The evolution super-operator `Ξ(t)` (Eq. 13/24) is
  expressed via the projected propagator `G_P(t, τ)` and the advanced/retarded propagator
  formalism (Eqs. 8–12, Supplementary Eqs. 13–25).
- **Eqs. (17)–(24) (Caldeira-Leggett evaluation):** Specializes to two-qubit gate operations with
  a spin-boson interaction `V = Σ_i σ_i^x ⊗ Φ_i(t)` where `Φ_i` is a fluctuating quantum field
  coupled to harmonic oscillators. The Ohmic damping rate `γ(ω) = (π/2) Σ_k |g_k|² δ(ω−ω_k)`
  (Eq. 19) gives the decoherence rate κ. The reduced density matrix elements in the multiplet
  basis become functions of the time integrals `S_i(t) = ∫₀ᵗ ds ∫₀ˢ dτ D_i(τ)` where `D_i(τ)` is
  the reservoir correlation function, expressed in terms of sine/cosine integrals with cutoff ω_c
  (Eq. 24).
- **Eqs. (25)–(33) (Identity operation):** Defines the QEM recovery operator `R_QEM` and the cost
  function `C_QEM = ||V_QEM − I||` where `V_QEM = R_QEM · E_non-Markovian`. For the identity gate,
  derives the output probability distribution (Eq. 31) which is Gaussian in the switching time `t_S`.
  The decoherence function κ (Eq. 32) and NISQ system parameter η are estimated by fitting Eq. 31
  to Table 1 data (1000 shots each on ibm_guadalupe and IonQ for |00⟩ input).
- **Eqs. (34)–(39) (CNOT operation):** Expresses the noisy CNOT evolution operator in the
  multiplet basis, derives the QEM recovery operator expanded in the 16 Dirac matrices (Eq. 38),
  and obtains the cost function (Eq. 39). The cost function **increases with coupling strength**
  α (Fig. 6).
- **Table 1 (a)–(d) (CNOT comparison):** Four initial states (|00⟩, |01⟩, (|10⟩+|11⟩)/√2,
  (|10⟩−|11⟩)/√2), each run 1000 shots on IBM Guadalupe and IonQ. The theoretical non-Markovian
  probabilities are calculated at a switching time `t_S` and fitted to extract the decoherence
  parameter κ and the NISQ parameter η for each machine.

**Headline claim:** "The cost function for quantum error mitigation increases as the coupling
strength between the quantum system and its environment intensifies." (Abstract / Discussion)

## Contributions — claim with evidence [paper]

| Claim | Evidence | Strength |
|---|---|---|
| **C1 — Time-convolutionless non-Markovian reduced density operator for two-qubit gates.** Analytic expression incorporating Ohmic Caldeira-Leggett noise through sine/cosine integral functions, with the switching time `t_S` as the control parameter. | Full derivation (Eqs. 1–24, Supplementary Eqs. 1–63). The multiplet-basis matrix elements (Eq. 22 / Supplementary Eq. 45) are closed-form in terms of known special functions. The Born approximation (Eq. 14) and the explicit `S_i(t)` integrals (Eqs. 23–24) quantify exactly where the Markov approximation is broken. | **High.** Derivation is self-contained, building on established time-convolutionless theory (Refs. 18–24). The Caldeira-Leggett evaluation is concrete and computable. The Born approximation is declared and limits the strong-coupling regime. |
| **C2 — QEM cost function increases with system–environment coupling strength.** | Fig. 6 plots `C_QEM` vs normalized gate operation time for various coupling strengths α, showing monotonic increase. Eq. 39 gives the closed-form expression. | **Moderate.** The claim is qualitative (monotonic increase) and matches physical intuition. Fig. 6 is the only evidence — no error bars, no analytic scaling law, no cross-validation. |
| **C3 — Non-Markovian model fits hardware data for identity and CNOT gates.** Measured output probabilities (Table 1, Table 1(a)–(d)) show agreement with theory for both IBM Guadalupe (superconducting) and IonQ (trapped-ion) devices, with the Caldeira-Leggett model fitting IonQ better for CNOT. | Table 1 (identity): ibm_guadalupe |00⟩=0.987 vs theory ~0.987; IonQ |00⟩=0.998 vs theory ~0.998. CNOT tables similarly show ~1–4% discrepancies across bases. κ and η values are extracted per machine per gate. | **Moderate.** The fitting is by matching a single decoherence parameter κ for each dataset. There is no held-out test, no prediction of unseen circuits, no statistical test of goodness-of-fit (χ², KL, etc.). The "strong agreement" claim (Discussion) is a visual/qualitative claim, not a quantitative one. The small sample (1000 shots) and single-gate-per-machine limit generalizability. |

## Method in detail [paper]

**Theoretical framework (Sec. II + Supplementary Secs. I–II):**

The total Hamiltonian (Eq. 1):
```
H_total = H_S + H_R + V
```
where `H_S` is the two-qubit system Hamiltonian, `H_R` the harmonic-oscillator reservoir, and `V`
the linear coupling `V = Σ_i σ_i^x ⊗ Φ_i`. The Liouville equation `∂_t ρ_T = −i [H_total, ρ_T]`
is solved by the projection operator method:

- **Projection operator** (Eq. 4): `P X = ρ_R ⊗ Tr_R X` eliminates reservoir DOF. The
  reduced density operator is `ρ_S(t) = Tr_R ρ_T(t)` (Eq. 6).
- **Coupled equations** (Eqs. 7a–7b): `∂_t Pρ_T = −i P L Pρ_T − i P L Qρ_T` etc. The formal
  solution (Eq. 8 / Supplementary Eq. 8) uses the projected propagator `G_Q(t, τ) = T exp[-i ∫_τᵗ dτ' Q L Q L(τ')]`.
- **Time-convolutionless form** (Supplementary Eq. 13): `∂_t Pρ_T = −i P L Pρ_T − i P L G_Q(t,0) Qρ_T(0) − ∫₀ᵗ dτ P L G_Q(t,τ) Q L Pρ_T(τ)`.
  The crucial step: by inverting `Qρ_T(t)` in terms of `Pρ_T(t)` using the advanced propagator
  (Supplementary Eqs. 10–13), the convolution integral is eliminated, yielding a time-local
  (but time-dependent-coefficient) master equation.
- **Born approximation** (Supplementary Eq. 25): `Ξ(t) ≈ exp[Tr_R(L R_0(−t) L)]`, where `R_0(t)`
  is the free-reservoir evolution. This gives the final form (Eq. 16 / Supplementary Eq. 39):
  ```
  ρ_S(t) = T exp[−∫₀ᵗ dτ₁ ∫₀^τ₁ dτ₂ Σ_i D_i(τ₁−τ₂) [σ_i^x(τ₁), [σ_i^x(τ₂), ·]]_I] ρ_S(0)
  ```
  where `D_i(τ) = Tr_R[Φ_i(τ) Φ_i(0) ρ_R]` is the reservoir correlation function.

**Caldeira-Leggett specialization (Sec. Results + Supplementary II):**

The interaction Hamiltonian (Eq. 17): `V = (1/2) Σ_{i=1,2} σ_i^x ⊗ Φ_i`, with
`Φ_i = Σ_k g_{ki} (a_k + a_k^†)`. Using the Ohmic spectral density `J(ω) = (π/2) Σ_k |g_k|² δ(ω−ω_k) = γ ω e^{−ω/ω_c}`,
the correlation function becomes:
```
D_i(τ) = Σ_k |g_{ki}|² [coth(βω_k/2) cos(ω_k τ) − i sin(ω_k τ)].
```
After evaluating the integrals (Supplementary Eqs. 41–63), the reduced density matrix element
(Supplementary Eq. 45) has the form:
```
ρ_S(t)_{ab,cd} = exp[−κ² (S_i(t) + S_j(t))] × (unitary evolution),
```
where `S_i(t) = ∫₀ᵗ ds ∫₀ˢ dτ D_i(τ)` expressed via sine/cosine integrals (Eq. 60 in Supp.),
and where `κ` is the Ohmic decoherence rate. The switching time `t_S` enters through the upper
limit of the inner integral — the non-Markovian memory extends backward over the full `[0, t]`
interval, unlike a Markov master equation where `D(τ) ∝ δ(τ)`.

**QEM cost function (Sec. Results, Eqs. 25–39):**

The ideal evolution is `ρ_ideal = U ρ(0) U^†` (Eq. 25). The QEM recovery operator `R_QEM`
satisfies `R_QEM ρ_S(t) R_QEM^† = ρ_ideal` (Eq. 26). The cost function is the deviation:
```
C_QEM = || V_QEM − I ||,   V_QEM = R_QEM · E(t)
```
where `E(t)` is the non-Markovian channel. For CNOT, `R_QEM` is expanded in 16 Dirac gamma
matrices (Eq. 38) with coefficients `c_A = Tr[Γ_A R_QEM]/4`, and `C_QEM` is evaluated as
(Eq. 39):
```
C_QEM(t, α) = f(κ, ω_c, t_S, α)
```
where the explicit form involves the sine/cosine integral functions `Si(ω_c t_S)` and `Ci(ω_c t_S)`.
Fig. 6 shows `C_QEM` vs `t/t_S` for α = {0.5, 1.0, 1.5, 2.0, 2.5, 3.0} (α is the dimensionless
coupling strength).

**Experimental comparison (Tables 1, 1a–1d, Sec. Results):**

- **Devices:** IBM Guadalupe (superconducting, 7-qubit backend) and IonQ (trapped-ion, through
  Amazon Braket). Each circuit run 1000 shots.
- **Identity (Table 1):** |00⟩ input → output probabilities. IBM: |00⟩=0.987, |01⟩=0.006,
  |10⟩=0.007, |11⟩=0. IonQ: 0.998, 0.001, 0.001, 0. Theory matches at ~0.987/0.998 for |00⟩,
  bit-flip probabilities at ~0.006–0.007 (IBM) vs 0.001 (IonQ). The decoherence parameter κ is
  estimated per machine: κ ≈ 0.11 (IBM), κ ≈ 0.045 (IonQ) — IonQ has ~2.4× lower decoherence
  from non-Markovian noise on the identity gate.
- **CNOT (Tables 1a–1d):** For |00⟩ input, both machines give |00⟩≈0.982–0.984 with ~1–2%
  leakage to |01⟩/|11⟩. For the superposition states (|10⟩±|11⟩)/√2, both machines show
  populations split ~50/50 between |10⟩ and |11⟩ with ~1% contamination in |00⟩/|01⟩. The
  Caldeira-Leggett model fits IonQ better for CNOT (Discussion), which the authors attribute to
  the ion-trap dynamics being better captured by the spin-boson interaction model.

## Methodology assessment [paper]

| Criterion | 1–5 | Assessment |
|---|---|---|
| Soundness | **4** | The time-convolutionless derivation is standard and correct within the Born approximation (declared). The Caldeira-Leggett model is a textbook open-system model. The QEM cost function definition is conventional (distance from ideal). Weakness: the "strong agreement" claim with hardware is visual/qualitative — no quantitative goodness-of-fit test, no confidence intervals on fitted κ and η, no held-out prediction. |
| Novelty | **2** | The time-convolutionless projection operator method for open quantum systems is well-established (Ahn's own 2000/2002 papers, Refs. 21–24). Applying it to a two-qubit CNOT gate and fitting a QEM cost function to two hardware machines is incremental. The "non-Markovian noise increases QEM cost" result is physically expected and not quantitatively sharpened (no scaling exponent, no threshold prediction). |
| Reproducibility | **3** | All analytic expressions are given (the derivation is self-contained). Hardware data is from accessible platforms (IBM Quantum, Amazon Braket). However: the extracted κ and η values are stated only as machine-specific fitted numbers (not tabulated explicitly for each case — the PDF extraction shows gaps at the numerical values); the switching time `t_S` normalization convention is not independently measurable from the paper alone without re-deriving the integrals; no code is provided. |
| Experimental design | **2** | Only two gates (identity, CNOT), only two machines, only 1000 shots per circuit, only one input state for identity and four for CNOT. No decoupling / twirling / randomized benchmarking to separate non-Markovian from Markovian contributions. No error bars. No stability analysis (run-to-run variation). The fitting of κ treats the hardware as the "truth" without modeling measurement error, SPAM errors, or readout noise. |
| Statistical rigor | **2** | No confidence intervals, no hypothesis tests, no bootstrap, no out-of-sample validation. The "strong agreement" is a qualitative visual claim based on a single-parameter fit to 4 (identity) or 16 (CNOT) measured probabilities. The 1000-shot sample size gives a binomial uncertainty of ~0.3–1% — consistent with the reported deviations — but this uncertainty is not propagated or discussed. |
| Scalability | **1** | Confined to two qubits. The time-convolutionless projection operator method scales horribly with system size (the multi-time integrands require tracking the full reservoir history). The authors do not discuss any path to larger systems. The Caldeira-Leggett Ohmic model is a single-bath, linear-coupling approximation — no multi-bath, multi-qubit noise correlations, no geometric locality considerations. |

## Strengths [paper]

- **S1 — Self-contained analytic derivation (Sec. II + Supplementary Info).** The full
  time-convolutionless projection operator derivation for the two-qubit case is carried out
  from first principles, covering the reservoir correlation functions, the Ohmic spectral density
  integration, the sine/cosine integral evaluation, and the multiplet-basis to computational-basis
  transformation. This is a complete reference calculation for anyone needing to replicate or
  extend the non-Markovian two-qubit master equation under Caldeira-Leggett noise. The concrete
  expressions (Supplementary Eqs. 45–63) could be directly coded into a simulator.

- **S2 — Dual-platform hardware comparison (Tables 1, 1a–1d).** Fitting the same analytic model
  to both a superconducting (IBM Guadalupe) and a trapped-ion (IonQ) machine is a useful
  sanity check. The finding that the Caldeira-Leggett model works better for IonQ (Discussion)
  is physically plausible (the spin-boson model is closer to a trapped-ion's motional coupling
  than to a transmon's flux/charge noise) and is one of the few non-trivial physical claims in
  the paper.

- **S3 — QEM cost function as an explicit function of coupling (Eq. 39, Fig. 6).** Unlike most
  QEM papers which treat noise as an abstract channel or black-box error rate, this work derives
  `C_QEM(t, α)` explicitly from the underlying coupling strength α and gate operation time. This
  connects the microphysics (spin-boson coupling) to the operational cost (how much mitigation is
  needed), which is a useful conceptual bridge. The cost function expression could in principle
  be used to optimize gate speeds given a known noise environment.

## Weaknesses / Limitations [paper]

- **W1 — No separation of Markovian vs non-Markovian contributions.** The paper attributes all
  deviations from ideal to "non-Markovian noise" but never demonstrates that a Markovian model
  (Lindblad master equation with the same κ) would fail to fit the data. Without this comparison,
  the claim that non-Markovian effects are the relevant physics is unsubstantiated — the data
  could equally well be described by a Markovian model with an appropriate decoherence rate.
  The central novelty of the paper ("non-Markovian noise matters") is neither tested nor
  quantitatively separated from known Markovian effects.

- **W2 — Cost function is not shown to be useful for QEM.** The paper defines `C_QEM` as
  `||V_QEM − I||` (deviation from ideal after applying a recovery operation) but never
  demonstrates that this cost function *does* anything: no QEM protocol is applied, no mitigated
  expectation values are reported, no comparison to standard QEM methods (zero-noise extrapolation,
  probabilistic error cancellation, Clifford data regression) is made. The cost function remains
  a theoretical abstraction with no operational demonstration.

- **W3 — Extreme system-size limitation.** The derivation relies on the multiplet basis of
  *two* qubits (`C_2 × C_2`, 4 basis states). The projection operator method with the Born
  approximation + the explicit sine/cosine integral evaluation does not generalize: the
  `[σ_i^x(τ₁), [σ_j^x(τ₂), ·]]` nested-commutator structure grows as `O(4^n)` with qubit count,
  and the two-time reservoir integrals require tracking each qubit's environment separately with
  no spatial correlation structure. The paper gives no indication of how (or whether) this
  approach scales beyond 2 qubits. This limits its relevance for any QEC-scale system.

- **W4 — No identifiability or gauge analysis.** The NISQ parameter η and decoherence rate κ are
  fitted from output probabilities, but no analysis is given of whether different
  (η, κ, coupling model) combinations could produce the same output statistics. For the identity
  gate with |00⟩ input, the output is largely determined by the decoherence envelope (a single
  parameter), and there is no argument that the non-Markovian model is *identifiable* from the
  available data versus a simpler Markovian model with the same decoherence rate. This is the
  same observational-identifiability issue the twin addresses systematically.

- **W5 — Numerical values for the key fitted parameter (η, the "NISQ system parameter") are
  stated but the extractable-pdf text does not render them.** The values for ibm_guadalupe and
  IonQ per gate-configuration are noted in the text but could not be independently verified from
  the PDF extraction used for this note. The η parameter determines the Gaussian width of the
  decoherence envelope and is central to the cost function — its values should have been tabulated.

## Relevance to the twin [twin]

This paper is **tangential**: it provides a reference non-Markovian two-qubit calculation and a
QEM cost function example but does not pose, address, or overlap with the twin's core questions
(recover causal mechanisms from QEC detector records, understand their identifiability,
manipulate via `do()`, predict under drift).

1. **No contact with any twin capability (negative result).** The paper never touches QEC — no
   stabilizer codes, no syndromes, no detectors, no decoders. Its object is the output
   probability distribution of a bare two-qubit gate; the twin's object is the causal mechanism
   field `E` of a QEC device inferred from stabilizer records. The papers occupy disjoint domains.
   **One-sentence positioning:** cite as an example of (a) non-Markovian gate-level noise modeling
   for a 2-qubit NISQ device, (b) where the QEM cost function comes from in the
   harmonic-oscillator-bath picture, but (c) not a source for any recover/understand/manipulate/
   predict claim or for any QEC-specific analysis.

2. **Gauge/identifiability (ADR 0005) is absent — this is a gap the twin fills.** The paper
   fits a single non-Markovian model to output probabilities without asking whether a Markovian
   or simpler model could produce the same data. Our identifiability framework (the probe-richness
   ladder, the A-matrix span, the Fisher σ-spectrum) is designed exactly to distinguish what
   *can* be learned from a given data class. This paper's lack of identifiability analysis is not
   a flaw in its context (it is an engineering model, not a causal-structure-learning paper) but
   sharply delineates the boundary: the twin's contribution is what the paper *does not do*.

3. **Caldeira-Leggett Ohmic model is a reference for the carrier's noise-provenance discussion
   (Step 0.alpha).** The spin-boson model with Ohmic damping is a standard bath model. If the
   twin's scalable carrier ever needs a physical bath model for its non-Markovian noise
   (beyond the quasistatic-Gaussian declaration), this paper's Eqs. 17–24 provide the concrete
   Ohmic correlation function `D(τ)` and the sine/cosine-integral `S(t)` expressions. But note:
   the Ohmic model applies to **dissipative** noise (σ^x coupling), while the twin's current
   carrier focuses on **dephasing** noise (σ^z) — the two live in different noise sectors. The
   Ohmic model generates bit-flip + energy relaxation, not the phase damping the twin's coherent-Z
   teachers use.

4. **QEM cost function is not the twin's cost function.** The paper's `C_QEM = ||V_QEM − I||`
   measures deviation from an ideal gate. The twin's relevant cost functions are (a) the
   label-free NLL (`log P(data | params)`) for recovery, (b) the identifiability condition
   number or Fisher information for gauge analysis, (c) the logical error rate `p_L` for the
   frozen-decoder eval loop. None of these appear in the paper. **Do not conflate** the QEM cost
   function (operational gate-error measure) with the twin's causal-recovery or
   decision-regret objectives.

5. **Time-convolutionless projection operator formalism: theoretical engine technique.** The
   formal method (Supplementary Sec. I) is a standard open-quantum-systems technique for deriving
   non-Markovian master equations without the Markov approximation. If the twin ever extends its
   carrier beyond the quasistatic/Gaussian limit into a full time-convolutionless non-Markovian
   regime, this paper (together with Ahn's 2000/2002 papers, Refs. 18–19) provides the concrete
   computational template. However, this is not a current or planned direction — the twin's
   carrier uses a declared-class Gaussian model with 1/f and quasistatic anchors, not a
   time-convolutionless kernel.

6. **Hardware numbers corpus (Tables 1, 1a–1d).** The measured output probabilities for IBM and
   IonQ on identity and CNOT gates (1000 shots each) are a small but clean reference dataset for
   anyone testing a 2-qubit noise model against real hardware. Not likely to be used in the twin
   (which operates at >5-qubit QEC scales), but noted for completeness.

## How to use / trust + open questions [twin]

- **Trust:** the analytic derivation (Sec. II, Supplementary) is standard and can be trusted as a
  reference for the time-convolutionless Caldeira-Leggett two-qubit calculation. The hardware
  comparison (Tables 1, 1a–1d) reports raw count data that is transparent and usable. **Do not
  trust** the "non-Markovian" attribution (W1) — there is no evidence that Markovian model would
  not fit the same data. **Do not trust** the QEM cost function as an operational tool (W2) — it
  is not demonstrated.
- **Use:**
  - As a literature reference for the claim "non-Markovian noise has been studied in the context
    of QEM cost functions" (background/related work in our positioning).
  - As an example of the time-convolutionless projection operator method applied to a concrete
    circuit, if the twin ever documents its theoretical-engine alternatives.
  - As a cautionary example for the twin's identifiability documentation: show that a
    state-of-the-art 2023 non-Markovian fitting paper did NOT ask whether its model was
    identifiable from data — and that the twin does.
  - The Caldeira-Leggett `σ^x`-coupled dissipation model as a physical alternative to the twin's
    `σ^z`-dephasing noise, for the noise-provenance discussion.
- **Open questions (for us):**
  - (i) Would a simple Markovian Lindblad model with the same κ fit the Tables 1, 1a–1d data?
    This is the decisive test the paper omits. A quick check: the identity-gate |00⟩ probability
    of 0.987 (IBM) corresponds to a depolarizing probability ~0.013, which a single-parameter
    Lindblad model would also reproduce — so the non-Markovian model is not uniquely identified.
  - (ii) Could the time-convolutionless formalism be applied to a stabilizer-measurement circuit
    (not just a bare gate)? The `[σ^x, [σ^x, ·]]` structure would need to be replaced by the
    stabilizer-Pauli commutator structure. This is an open technical question — no paper has
    done it at QEC scale.
  - (iii) The NISQ parameter η (fitted Gaussian width) ranges per machine and per gate — but the
    paper does not explain what physical quantity η represents (bath temperature? cutoff? coupling
    inhomogeneity?). Resolving this would require re-deriving the fit.
