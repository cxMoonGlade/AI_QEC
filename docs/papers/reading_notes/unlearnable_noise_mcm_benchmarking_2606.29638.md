# Deep review -- Cheng et al., "Characterization of Unlearnable Noise with Mid-Circuit-Measurement-Based Cycle Benchmarking"

> **Provenance (2026-07-02): arXiv HTML deep read.** Full theorem-by-theorem read of Sections I-V (all 8 numbered results: Def. 1, Thm. 1-6, Lemma 1) and Appendices A-E. Experimental results verified against stated figures. No supplementary PDF parsed; the arXiv HTML v2 served as primary source (all equations, figures, and tables extracted).

## Metadata

- **Authors:** M. H. Cheng (Imperial College London & Fraunhofer ITWM), Stefano Mangini (Algorithmiq Ltd & U. Helsinki), V. Bartsch (Fraunhofer CML), A. C. Medina (Fraunhofer ITWM), Sergey N. Filippov (Algorithmiq Ltd), Matteo A. C. Rossi (Algorithmiq Ltd), M. S. Kim (Imperial College London).
- **Venue / status:** arXiv:2606.29638v2 [quant-ph], 30 Jun 2026 (v1 28 Jun 2026). No journal assignment yet.
- **Domain / type:** Quantum noise characterization; **theory + experiment** (numerical simulation + superconducting QPU validation).
- **One-line.** Standard cycle benchmarking leaves coupled Pauli fidelities unidentifiable; inserting mid-circuit measurements at the qubits where the Pauli weight pattern changes -- quantified by a single binary vector delta -- breaks the gauge degeneracy and makes previously unlearnable noise components learnable, with a binomial diagnostic for non-Markovianity.

## Executive summary

The paper tackles the fundamental identifiability gap in cycle benchmarking (CB): for a general n-qubit Clifford gate G, most Pauli fidelities lambda_{P_beta} are unlearnable because the input Pauli P_alpha and output P_beta = G(P_alpha) have different support (Def. 1's delta = pt(P_beta) XOR pt(P_alpha) != 0). This is the exact same gauge degeneracy Chen (2206.06362) characterized as the cut-space of the pattern transfer graph.

The authors show that inserting mid-circuit measurements (MCMs) at exactly the qubit locations where delta != 0 reverses the Pauli propagation, making the previously coupled fidelities individually learnable. The key enabler is the **deferred feed-forward principle** (Lemma 1): the classical conditional bit-flips that implement the reversal are computed offline and applied in post-processing, requiring no real-time quantum feedback. The framework is built on two measurement instrument models -- uniform stochastic instruments (USI) and quantum instruments with classical feed-forward (QICF) -- and yields closed-form exponential fidelity decays (Eqs. 39-43) that separate classical readout error from quantum Pauli fidelities.

A secondary contribution is the **binomial diagnostic** (Section I.3): under a Markovian separable-USI model, the flip-variable distribution is exactly binomial (Eq. 38); classical readout asymmetry produces a characteristic zig-zag deviation, and non-Markovian memory produces exponential tails. The framework is validated on ibm-aachen and ibm-pittsburgh, achieving CPTP-bounded characterization of CNOT unlearnable pairs and detecting measurement-induced bit-flip bias and leakage-induced non-Markovian correlations.

## Contributions (claim -> evidence -> strength)

- **C1. MCM-based learnability condition for Clifford gates (Thm. 1 + Thm. 6).** A Pauli fidelity lambda_{P_beta} is learnable iff MCMs are inserted at the qubit locations specified by delta(P_alpha, P_beta) (the Pauli weight-pattern mismatch). *Evidence:* Thm. 1 restates Chen's condition (delta=0 learnable without MCMs); Thm. 6 shows that MCMs at the |delta| mismatch qubits reverse the propagation and make the fidelity learnable. The number of MCMs equals |delta|, quantifying the resource overhead. *Strength: strong -- theorem statements with explicit construction; the cost measure (Hamming weight of delta) is a clean operational quantity.*

- **C2. Deferred feed-forward principle (Lemma 1).** No real-time quantum feed-forward is needed; all classical conditional operations can be deferred to classical post-processing without changing the measurement statistics. *Evidence:* explicit construction using a perfect ancillary qubit (Eq. 27) and its replacement by a classical bit. *Strength: strong, proof-sketch level; the principle is critical for experimental feasibility.*

- **C3. Separation of classical readout error from quantum fidelity (Eqs. 39-43).** The combined generalized CB decay f_{GCB}(d) factorises into a readout-error product (1-2q_p) and the fidelity lambda_{P_beta}, enabling independent characterization. *Evidence:* analytical derivation; demonstrated on hardware. *Strength: strong -- closed-form, no iterative fitting needed.*

- **C4. Binomial non-Markovianity diagnostic (Section I.3, Eq. 38).** Flip-variable statistics follow a clean binomial under Markovian separable-USI; deviations signal non-Markovian dynamics (classical asymmetry -> zig-zag, leakage -> exponential tail). *Evidence:* Section I.3 derivation; hardware observation of both deviations (Section IV.2). *Strength: strong -- useful diagnostic, though the assumption of separable USI limits generality.*

- **C5. Hardware demonstration of unlearnable noise characterization (Section IV).** Extracted CNOT unlearnable pairs on ibm-aachen/ibm-pittsburgh within CPTP bounds, surpassing direct fidelity measurement precision. Observed measurement-induced bit-flip bias and non-Markovian memory. *Evidence:* Section IV.1-2 experiment descriptions. *Strength: moderate -- single-device demonstration without error bars or statistical tests claimed against a tomography ground truth.*

## Method (deep)

### The identifiability gap (Def. 1, Thm. 1)

For an n-qubit Clifford gate G with Pauli noise channel Lambda, the noisy gate is Lambda ∘ G. Standard CB measures decay of the form:

f(N) = Tr[P_beta (Lambda^N(G(rho)))] = A lambda_{P_beta}^N + B

But when the input Pauli P_alpha and output P_beta = G(P_alpha) have different support, the observable factorises into products of fidelities that cannot be individually resolved (Eq. 8 for CNOT: lambda_{0i} lambda_{jk} product).

**Paul weight mismatch** (Def. 1): delta(P_alpha, P_beta) := pt(P_beta) XOR pt(P_alpha) in {0,1}^n, where pt(P) records locations of non-identity Paulis. **Thm. 1**: lambda_{P_beta} learnable iff delta = 0 (no weight-pattern change). This is Chen's condition.

### USI model (Section I.2.1)

A uniform stochastic instrument (USI) for l measured qubits (Eqs. 11-12):

M_o(rho) = sum_{r,k} q_r M_k(rho) tensor e_{k+r}

M_k(rho) = sum_{a,b} p_{a,b} [Lambda_{a,b} tensor X^b |k><k| X^a](rho)

where q_r are classical readout assignment errors, p_{a,b} quantum transition probabilities, and Lambda_{a,b} post-measurement Pauli channels.

**Thm. 2 (Pauli propagation for USIs):** A single-qubit USI, averaged over outcomes, acts as a Pauli channel on Z-type observables and commutes with bit-flip operations (Eqs. 14-17). Key constraint: Z propagation factor delta_Z = p_00 lambda_00 + (-1)^c p_10 lambda_10 + (-1)^c p_01 lambda_01 + p_11 lambda_11.

**Thm. 3 (Exact noise extraction):** All Pauli fidelities of a single-qubit USI are learnable if p_01 = p_11 = 0 (no quantum errors after measurement projection). Classical readout errors q_r do not affect learnability. The learnable triplets are {p_{a,0}, Lambda_{a,0}, q_r} (Eq. 19).

**Thm. 4 (Approximate extraction):** With high-fidelity |0> preparation alone, CNOT Pauli fidelities can still be approximated via post-selection on the MCM readout returning |0>. Post-selection provides access to both the geometric mean (standard CB) and the approximate arithmetic mean of each unlearnable pair, allowing mathematical isolation.

### QICF model and reversal (Section I.2.2)

A quantum instrument with classical feed-forward (QICF, Eqs. 20-21) uses the classical readout outcome to conditionally apply bit-flips on a subset of qubits:

Ctrl-M(rho) = sum_{r,k} q_r C_{k,r}(rho) tensor e_{k+r}

C_{k,r}(rho) = M_k[(X^{M(k+r)} tensor I^{otimes l})(rho)]

where M is an m x l linear transformation mapping readout to conditional bit-flips.

**Thm. 5 (Pauli propagation for stochastic CNOT):** A stochastic CNOT (Eqs. 22-23) implements a controlled-NOT on the classical register -- the averaged channel replicates a coherent CNOT on Z-type observables up to classical-readout-error scaling (Eqs. 25-26).

**Lemma 1 (Deferred feed-forward):** The conditional bit-flips can be computed classically and applied in post-processing. Proof: a perfect ancillary qubit extends the Pauli operator to Z_0 tensor P_beta; stochastic CNOTs with single-qubit Cliffords yield the reversal map (Eq. 27):

R_{delta(P_alpha,P_beta)}(Z_0 tensor P_beta) = lambda Z_0 tensor P_alpha

Since the ancilla remains unentangled, it is replaced by a classical bit.

**Thm. 6 (MCM resource cost):** The number of MCMs required equals |delta(P_alpha,P_beta)|. Three implications: no full tomography, no additional Clifford gates, no post-selection (all feed-forward deferred).

### Binomial diagnostic (Section I.3)

Define the flip variable f_{p,i} = k_{p,i-1} XOR k_{p,i} for MCM outcome k_{p,i} at qubit p and cycle i. Under Markovian separable-USI, f_{p,i} is i.i.d. The distribution over total flips f = sum_i f_{p,i} is purely binomial after averaging:

p(f) = C(N,f) ((1 + lambda_{P_p})/2)^{N-f} ((1 - lambda_{P_p})/2)^f   (Eq. 38)

Deviation from binomial signals non-Markovianity. Classical readout asymmetry produces a characteristic zig-zag pattern (alternating f-parity bins, Fig. 3); leakage produces exponential tails.

### Combined generalized CB decay (Section II)

The key operational result (Eq. 43):

f_{GCB}(d) = A [ prod_{p in delta} (1-2q_p) delta_{P_beta} lambda_{P_beta} ]^d + B

where q_p are classical readout errors, delta_{P_beta} the reversal channel's Pauli fidelity, and lambda_{P_beta} the target Clifford-gate fidelity. The product separates readout error from quantum noise.

## Results

### Numerical simulations (Section III)

**CNOT exact learning (Section III.1.1, Fig. 4).** R=1000, S=1000 per data point. MCM noise learning resolves the coupled pairs {lambda_{x0}, lambda_{xx}} and {lambda_{0z}, lambda_{zz}} with exponential decays. Classical readout errors (Re1, Re2) separated from quantum fidelities.

**CNOT approximate learning (Section III.1.2, Fig. 5).** R=1000, S=10000 per data point. Reliable |0> preparation alone suffices (Thm. 4) with single-qubit y-rotation before each MCM. Optimal angles cos 14, cos 18, cos 22 degrees shown. Extraction quality degrades with state-preparation infidelity.

**Three-qubit CNOT ladder (Section III.2, Fig. 6).** R=250, S=100 per data point. Without locality knowledge, MCMs needed at both delta locations simultaneously; with local noise structure, overhead reduces.

### Hardware experiments (Section IV)

**Platforms:** ibm-aachen, ibm-pittsburgh.

**Unlearnable noise learning (Section IV.1):** Extracted CNOT unlearnable fidelity pairs within CPTP bounds, surpassing direct fidelity measurement precision.

**Binomial analysis (Section IV.2):** Three findings -- (i) flip-variable statistics roughly binomial, consistent with Markovian separable-USI as baseline; (ii) **measurement-induced bit-flip bias** attributable to classical readout asymmetry (systematic deviation from symmetric binomial); (iii) **leakage-induced exponential tail** in the flip distribution, providing a quantitative non-Markovianity signature invisible to standard CB.

## Methodology assessment

| Criterion | 1-5 | Assessment |
|---|---|---|
| Soundness | **5** | Theorems 1-6 and Lemma 1 are well-formed results with explicit assumptions (noiseless single-qubit Cliffords, separable USI for binomial diagnostic). The delta-condition framework is mathematically clean. Some proof sketches rather than full appendix proofs (e.g., Lemma 1's ancilla argument is constructive but a full optimality proof would strengthen). |
| Novelty | **4** | The core idea (MCMs break Pauli gauge degeneracy) is conceptually novel and directly addresses the Chen gap. The deferred feed-forward principle is elegant. The binomial non-Markovianity diagnostic is genuinely new. However, the learnability machinery (Thm. 1) heavily extends Chen 2206.06362; the paper is an evolution of known ideas rather than a discontinuous advance. |
| Reproducibility | **3** | Protocols specified (R,S counts, error models), and fake-torino calibration is referenced for numerical work. But hardware results are single-lab on two IBM processors; no public code/data link in the abstract text. The protocol is sufficiently described to be re-implemented. |
| Experimental design | **4** | Numerical demonstrations are systematic (depolarizing model + real-calibration noise); hardware validation against conventional tomography is the right benchmark. Weakness: single device generation (two chips are similar IBM Heron family), no cross-platform comparison, no error-bars on hardware claims vs tomography. |
| Statistical rigor | **3** | Numerical simulations use controlled error models with explicit R,S. But: no sample-complexity analysis for the binomial diagnostic (how many shots to detect a given non-Markovian deviation?), no uncertainty quantification on the hardware-extracted fidelities beyond CPTP-bound compliance. The "surpassing direct fidelity precision" claim lacks an explicit statistical test. |
| Scalability | **4** | The cost measure (|delta| MCMs per fidelity) is favorable: it scales with the Hamming weight of the pattern mismatch, not with 4^n or the full gate set. The binomial diagnostic needs O(N) shots per qubit. However, the framework currently applies per gate/prefix (single G at a time), and scaling to many-qubit parallel gates is not analyzed. |

## Strengths

- **S1 -- The delta characterisation (Def. 1, Thm. 6).** Mapping the identifiability gap to a single binary vector delta = pt(P_alpha) XOR pt(P_beta) and quantifing the MCM resource cost as |delta| (Hamming weight) is clean, operational, and practically useful: an experimentalist immediately knows which qubits to measure and how many MCMs are needed. This transforms Chen's graph-theoretic characterisation into an implementable protocol specification.

- **S2 -- The deferred feed-forward principle (Lemma 1).** Showing that MCM-based generalized CB requires no real-time quantum feedback is a critical practical contribution. It means the protocol runs on any QPU with mid-circuit measurement capability and classical control -- no need for fast feedback loops or dynamic circuit compilation. This extends the hardware accessibility significantly.

- **S3 -- The binomial non-Markovianity diagnostic (Section I.3.2, Eq. 38).** The observation that under a Markovian separable-USI model the flip-variable distribution is exactly binomial, and that specific deviations (classical asymmetry, leakage) produce distinct signature patterns, provides a quantitative, parameter-free non-Markovianity detector. This is a significant advance over standard CB which is blind to non-Markovian effects. The zig-zag readout-asymmetry pattern (Fig. 3) and the exponential leakage tail are concrete experimental signatures.

## Weaknesses / limitations

- **W1 -- Relies on noiseless single-qubit Cliffords and the Pauli-twirled noise model (same assumption set as Chen).** The paper inherits Chen's W1/W3: everything is Pauli-diagonal noise (Eq. 4), no coherent content survives the twirl, no continuous noise fields. The MCM structure is modeled as USI with Pauli channels on post-measurement states -- all non-Pauli dynamics (leakage is diagnosed but not modeled within the USI framework, only flagged as non-Markovian residual). This is the same discrete-Pauli ceiling the twin targets with its continuous-GKSL learner.

- **W2 -- No unified gauge analysis.** The paper shows that specific product fidelities become learnable when MCMs are inserted, but does not provide a full characterisation of the new gauge structure after MCM insertion. Chen's graph-theoretic framework (cycle space / cut space) gave a complete picture of what remains unlearnable; this paper's protocol similarly needs a gauge theorem showing "after MCM insertion, the remaining unlearnable subspace is X." Thm. 6's |delta|-cost gives the MCM count but not the post-MCM identifiability algebra -- the state after the protocol is "some parameters learnable" but the residual gauge (if any) is uncharacterised.

- **W3 -- Hardware validation limited in scope.** Two IBM Heron processors from the same family, single gate type (CNOT), no cross-platform or temporal variation (drift). The binomial diagnostic's non-Markovian signatures (measurement-induced bit-flip bias, leakage tail) are observed but not quantitatively validated against an independent ground-truth non-Markovianity measure. The "surpassing direct fidelity measurement precision" claim lacks an explicit comparison with uncertainty intervals.

- **W4 -- Binomial diagnostic's separable-USI assumption (Eqs. 35-36) is restrictive.** The clean binomial result requires that pre- and post-measurement effects factorise (Lambda_{ab} = Lambda_a Lambda'_b, p_{ab} = p_a p'_b). When this fails, the distribution deviates from binomial even under Markovian dynamics, confounding the non-Markovianity diagnostic. The paper identifies this boundedly (it limits the diagnostic to separable USI) but does not characterise how much non-separable-but-Markovian dynamics corrupt the test.

## Relevance to the twin

### 1. MCMs as a probe-richness lever for the discrete-Pauli gauge (direct Chen/Zheng extension)

The paper's central claim -- that MCMs break the gauge degeneracy in CB -- is a **direct operational extension of the Chen/Zheng gauge framework** this project builds on. Chen (2206.06362) proved that Pauli fidelities are learnable iff their pattern is preserved (delta=0), with the cut-space as the unlearnable subspace. This paper shows that adding MCMs at the delta locations makes those cut-space directions learnable.

For the twin's positioning, this matters because:

- **The Chen gauge is not absolute -- it is protocol-relative.** This paper proves concretely that extending the access model (adding MCMs) shrinks the gauge: what was unlearnable in standard CB becomes learnable. This confirms the twin's principle that the "learnable-DOF ceiling" (Zheng 2601.22286) is conditional on the measurement protocol, not a fundamental limitation of the Pauli noise model itself.

- **Delta is a probe richness metric.** The Hamming weight |delta| = number of qubits where the Pauli weight pattern changes serves as a **quantitative measure of how many MCMs are needed to break the gauge** for a given gate-fidelity pair. The twin's `C_cal(r)` probe-richness ladder should include an analogous resource count: how many detector rounds / MCM insertions are needed to shrink the gauge to a target size.

- **Their USI gauge-free result (Thm. 3) maps to our exact-learnability ceiling.** The condition p_01 = p_11 = 0 says "no quantum errors after measurement projection" removes all unlearnability. In our setting, the analogous statement is: if the measurement backaction is known and deterministic (a known CP map, not an unknown mixture), then the MCM introduces no new identifiability ambiguity.

### 2. Continuous-Sigma extension: what this paper does NOT cover (the gap our twin targets)

This paper stays in the discrete-Pauli world. Its contributions are:

- Discrete Pauli fidelities lambda_{P_beta} (scalars on the Boolean lattice).
- Pauli twirled noise (Eq. 4) -- no coherent content.
- Fixed gate sets, not continuous channels.
- MCMs as classical-projective measurements, not as part of a continuous covariance estimation.

Our twin's continuous-Sigma extension of the Pauli gauge framework targets exactly the regime this paper does not cover:

- Continuous Gaussian noise fields (spacetime covariance Sigma) replacing discrete Pauli parameters.
- Passive detector records (fixed syndrome circuits) replacing active CB-style depth ladders.
- Non-Pauli / coherent mechanisms.
- Non-Markovianity modeled as temporal covariance, not just a binomial deviation flag.

**The complementarity is productive:** Their paper shows how far the discrete-Pauli gauge can be shrunk with active MCM insertion; our twin shows what happens when you move off the discrete-Pauli frame entirely. The twin should cite this paper as the state-of-the-art for MCM-enhanced discrete-Pauli CB, and position its own continuous-Sigma extension as the natural next step beyond the Pauli ceiling.

### 3. Binomial diagnostic as a Bone B/C record-classicality test

The binomial diagnostic (Eq. 38) is a **non-Markovianity detector for MCM sequences** that is directly relevant to the twin's Bone B/C work on record-classicality:

- Their flip-variable f_{p,i} = k_{p,i-1} XOR k_{p,i} is a **binary-valued time series** recording whether the MCM outcome changed between consecutive cycles. The binomial distribution under Markovian separability is a **baseline hypothesis test**: deviation => non-Markovian dynamics.
- The two signature patterns -- classical-readout zig-zag and leakage exponential tail -- correspond to different physical mechanisms that the twin's Bone C work aims to discriminate.
- The test requires only the MCM readout sequence, no additional instrumentation: it is a **passive diagnostic** derived from the same data used for fidelity extraction.

For the twin: this diagnostic should be **adapted to stabilizer-measurement sequences**, where each detector = parity of consecutive syndrome measurements. The twin's workspace (`docs/twin_validation/`) already records flip-like variables from syndrome repeats; the binomial test provides a quantitative non-Markovianity discriminator for these records, complementing the moment-based detectors.

### 4. The deferred feed-forward principle (Lemma 1): architectural insight for the twin's backward / composed carrier

The observation that the reversal channel can be implemented classically in post-processing (no real-time quantum feedback) is relevant to the twin's **composed carrier** (ADR 0008):

- The composed carrier stitches window-exact CPTP corrections across a DEM/HMM bulk. The correction protocol requires knowing which past errors propagated into the current window -- a "reversal" of sorts.
- Lemma 1 shows that **classical post-processing suffices for reversal** when the operation is Clifford + MCM. The composed carrier's window-correction logic may admit a similar deferred-feedforward formulation.
- More broadly, the principle that "computing the inverse Pauli frame classically rather than implementing it quantumly" reduces quantum resource requirements without changing the statistics is a design pattern the twin's scalable carrier should adopt.

### 5. Gauge comparison: MCM-based gauge-breaking vs. our gauge-parameterisation

| Property | This paper | Our twin |
|---|---|---|
| **Noise model** | Pauli-diagonal, discrete lambda_{P_beta} | Continuous Gaussian field Sigma |
| **Gauge origin** | Pattern-mismatch delta != 0 (cut space) | Non-identifiability in Sigma's spectral decomposition |
| **Gauge breaking** | MCM insertion at delta locations | Probe richness (multi-round, multi-context) + prior constraints |
| **Cost measure** | |delta| MCMs per fidelity pair | Number of detector rounds R, probe contexts |
| **Residual gauge** | Not characterised (W2) | PSD cone constraints + Bode/Bochner bounds |
| **Non-Markovianity** | Binomial deviation flag (qualitative) | Continuous temporal covariance model |
| **Validation** | Hardware vs conventional tomography | Exact independent-DM oracle (Anchor/Control ports) |

The comparison highlights a gap in this paper: it does not provide a **post-MCM gauge theorem** stating what remains unidentifiable after MCM insertion. The twin's approach of characterising the residual gauge as the null space of Hessian H (identifiability analysis) is more complete in this respect.

## How to use / trust + open questions

### Trust

- **High** for the theorem framework (Thm. 1-6, Lemma 1) and the delta condition. These are clean mathematical results with explicit assumptions.
- **Moderate** for the hardware validation: single device family, no statistical comparison against ground truth, no public data. The "surpassing direct fidelity measurement" claim needs independent replication.
- **High** for the binomial diagnostic derivation; the diagnostic itself is novel, but its separable-USI assumption (W4) limits its scope in the twin's more general setting.

### Use in the twin

- **Cite as:** a protocol-level extension of the Chen gauge framework that uses MCMs as the probe-richness lever to shrink the unlearnable subspace. Position it alongside Chen (2206.06362) and Zheng (2601.22286) as the three-pillar Pauli learnability literature: Chen = characterisation, Zheng = syndrome-data conditions, this paper = MCM-based gauge breaking.
- **Adopt the binomial diagnostic** as a Bone C record-classicality test for MCM-like measurement sequences (stabilizer rounds). Implement the flip-variable f_{p,i} and test against the binomial null in the rep-code and surface-code teachers.
- **Adopt the delta cost measure** as a template for quantifying probe richness in the twin's `C_cal(r)` ladder: |delta| = number of MCMs needed parallels R = number of rounds needed to break the alias.
- **Extend the deferred feed-forward principle** to the composed carrier's window correction: if the reversal of propagated errors can be deferred to classical post-processing, the composed carrier's quantum overhead decreases.

### Do not use for

- Continuous noise models (our Sigma extension is needed for that).
- Coherent/non-Pauli mechanisms (the Pauli twirl erases them).
- Full gauge characterisation after protocol application (the paper does not provide it).
- Non-separable USI settings (the binomial diagnostic may false-flag Markovian non-separable dynamics as non-Markovian).

### Open questions for the twin

1. **Post-MCM gauge algebra.** This paper shows that MCMs make specific fidelity pairs learnable, but does not provide a full gauge characterisation similar to Chen's cycle/cut space. Can the Chen pattern-transfer-graph be extended to include MCM edges, producing a new gauge decomposition with the post-MCM learnable/unlearnable subspaces? This would complete the framework.

2. **Binomial diagnostic for stabiliser rounds.** Can the flip-variable f_{p,i} = k_{p,i-1} XOR k_{p,i} be adapted from single-qubit MCM outcomes to multi-qubit parity measurements? The stabiliser measurement outcome at round i plays the same role as k_{p,i}; XOR across consecutive rounds gives a detector-like variable. If the binomial diagnostic works for detector-valued records, it provides an immediate non-Markovianity test for surface-code data.

3. **Resource-optimal MCM placement.** Thm. 6 gives the cost as |delta|, but for multi-qubit gates with multiple coupled pairs, the same MCM may serve to resolve multiple deltas simultaneously. What is the minimal set of MCM locations to make all fidelities of a gate set learnable? This is a covering problem on the pattern transfer graph.

4. **Relationship to the Chu MCM backaction paper (2606.00433).** Chu et al. characterised single-qubit MCM instruments via a continuous gauge (t in R(t)) under Z-twirling. This paper uses a Pauli-twirled USI model for MCMs but does not analyse the MCM backaction gauge in the same depth. Merging the two frameworks -- Chu's continuous gauge for the MCM instrument + this paper's delta-condition for the Clifford gate -- would give a unified MCM+gate learnability theory.

5. **Scaling to surface-code-size circuits.** The protocol is demonstrated on single CNOT and three-qubit CNOT ladders. How does the MCM overhead (|delta| per gate per fidelity) scale for a full surface-code syndrome extraction circuit with hundreds of parallel entangling gates? Does the deferred-feedforward principle permit efficient post-processing for circuit-level CB?
