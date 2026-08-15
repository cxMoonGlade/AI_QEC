# Reading note: Oda, Schultz, Norris, Shehab & Quiroz, "Sparse Non-Markovian Noise Modeling of Transmon-Based Multi-Qubit Operations" (arXiv:2412.16092)

> **Provenance (2026-07-06): full-text close-read (all main sections I–VII + appendices A–J
> scanned; verbatim quotes checked against the PDF text).** Source: cached PDF
> `docs/papers/2412.16092_sparse_nonmarkovian_transmon.pdf` (arXiv v1, 2024-12-20 — the only
> arXiv version as of 2026-07-06), text-extracted via `pdftotext`. Supersedes the earlier
> skim note `docs/papers/2412.16092_NOTES.md` (pp. 1–6 only) for paper-content questions.
> This note reports the paper's content only.

## Metadata [paper]
- **Authors:** Yasuo Oda (JHU), Kevin Schultz (JHU/APL), Leigh Norris (JHU/APL),
  Omar Shehab (IBM Quantum), Gregory Quiroz (JHU + JHU/APL)
- **Venue / status:** arXiv:2412.16092 [quant-ph], v1 2024-12-20 (single version).
  arXiv page lists a related APS journal DOI `10.1103/lx8x-z29x` (PRX Quantum
  publication [ours — APS page not directly fetchable; DOI prefix + redirect to
  link.aps.org confirmed]). License: CC BY 4.0.
- **Type:** methods + hardware characterization (IBM Quantum Platform transmons);
  hybrid Lindblad-master-equation / stochastic-Hamiltonian / channel noise model.

## Executive summary [paper]
A sparse, effective gate-level noise model for IBM fixed-frequency transmons, combining
three tiers: (1) *locally Markovian* dissipation (GAD/T1 with thermal excited-state
probability q, phase damping, control bit-flip dissipation, SPAM as a pre-measurement
bit-flip channel); (2) *extended Markovian* — spatial correlations modeled by enlarging
the qubit register with additional two-level quantum degrees of freedom (spectator qubits,
effective-qubit TLSs) coupled through always-on ZZ terms; (3) *stochastic* — classical
Gaussian wide-sense-stationary dephasing β_j(t) and control ε_j(t) processes in a
stochastic Hamiltonian, characterized by PSDs via QNS/FTTPS and simulated by trajectory
averaging. "The model is parameterized by ten parameters per qubit and three parameters
per qubit pair" (Sec. I). Characterized on "39 qubits across seven devices" (Sec. I);
validated on RB, CPMG/multi-qubit DD, repeated-ECR, and a 2-qubit VQE (H2), where "our
noise model obtains a relative error of ∆(Ropt) ≈ 0.5%, a 7× improvement over the default
model" (Sec. V B). Sec. VI gives a composite-channel reduction of the LME model for
scalability.

## Q1 — Hilbert space: what the "extension" is (no leakage anywhere)

**The model Hilbert space is qubits-only (2-level systems throughout).** The "extension"
= appending *ancilla-like two-level quantum degrees of freedom* (spectator qubits and
effective-qubit TLSs) to the data-qubit register, plus *classical* stochastic variables.
It is NOT an extension to higher levels: there is no |2⟩, no qutrit/qudit structure, no
transmon anharmonicity, no leakage anywhere in the model (system, ancilla, or embedding).

- Sec. II (model definition): "H(t) acts on the Hilbert space H = H_D ⊗ H_Sp ⊗ H_TLS,
  where the subspace H_D defines the Hilbert space for the data qubits, i.e., the qubits
  that will be employed for a particular sequence of gate operations. Spectator qubits
  that impose unwanted external coupling on the data qubits are defined under H_Sp.
  Lastly, H_TLS denotes the inclusion of fluctuating TLSs that couple to the data qubits."
- Sec. II C (TLSs are two-level, qubit-like): "TLSs are defined on a computational basis
  {∣0⟩_TLS, ∣1⟩_TLS} with Pauli operators σ_{µ,TLS}^{(j,k)}, for µ = x, y, z, qubit j and
  TLS k." — and "At the beginning of each experiment, all TLSs are considered to be
  initialized in the ∣+⟩ state."
- Sec. II C (what "extended Markovian" means): spatially correlated noise "can be modeled
  via LME by enlarging the data qubit system to include the additional quantum degrees of
  freedom [72, 78]"; Sec. IV B: "These processes are non-Markovian effects when viewed
  locally, but are well modeled with a LME by extending the system Hilbert space to
  include TLS and spectator qubit degrees of freedom."
- Sec. IV B 1: "we treat the TLS as an effective qubit that couples to the main qubit via
  a static ZZ interaction." Appendix A 4 d: "The single-qubit system is enlarged to a
  qubit+TLS system interacting via a ZZ coupling". Sec. VI B: the ZZ Hamiltonians "are
  diagonal in the n-qubit+TLSs computational basis".
- The temporal (stochastic) part is explicitly classical, not extra quantum levels —
  Sec. I: "System operators couple to stochastic, time-dependent, variables as opposed to
  additional quantum degrees of freedom."
- [ours] Negative scan of the full extracted text: zero occurrences of "leakage",
  "qutrit", "|2⟩", "anharmonic(ity)", "higher level(s)", "third level". The single
  "qudit" occurrence is prior-work citation only — Sec. I: "The formalism has been
  employed in studies of spatio-temporally correlated noise in single [73, 74] and
  two-qubit [75], as well as qudit [76], systems." (about the stochastic-Hamiltonian
  literature, ref [76] = Sung et al., Nat. Commun. 12, 967 (2021), not their model).

## Q2 — QEC syndrome records: none

**The paper neither simulates nor generates QEC syndrome data and applies the model to no
QEC experiment.** Validation is confined to: the characterization circuit suite,
randomized benchmarking, CPMG / multi-qubit dynamical decoupling, repeated ECR gates, and
a 2-qubit VQE.

- The only QEC mention in the paper is a background citation list — Sec. I: "The benefits
  of many of these approaches have been showcased on superconducting hardware via
  demonstrations of dynamical decoupling (DD) [30–34], decoherence-free subspaces
  [35–37], quantum error correcting codes [38–44], and various quantum error mitigation
  protocols [45–48]."
- Abstract (the actual validation targets): "The model's predictive power is further
  highlighted through multi-qubit dynamical decoupling demonstrations and an
  implementation of the variational quantum eigensolver."
- Sec. III A (all experiments run): "the set of single-qubit experiments
  C1 = {M, T1, T2, P, Q}, and two-qubit experiments C2 = {XT, CR}"; Sec. IV adds RB and
  CPMG; Sec. V adds multi-qubit XY4 DD and VQE (H2).
- [ours] Negative scan: zero occurrences of "syndrome", "detector", "detection event",
  "surface code", "repetition code" in the full text; "stabilizer" appears only inside
  the reference-list title of Gottesman [20]. No decoder, no detector error model, no
  {det,obs}-type records.

## Q3 — Noise axes covered + demonstrated scale

**Covered axes** [paper, Sec. II]:
- *Temporal non-Markovian (classical):* stochastic Gaussian wide-sense-stationary
  dephasing β_j(t) and control ε_j(t) noise in H_N,1(t) (Eq. 10); "These stochastic noise
  variables are assumed to be Gaussian and wide-sense stationary" (Sec. II D). PSDs
  reconstructed via QNS/FTTPS; the fitted dephasing PSD "strongly overlaps with a
  Lorentzian-like spectrum S_L(ω; α) = S0 / (1 + (ω/ω_max)^α)" (Eq. 20, Sec. IV C 1),
  "consistent with previous findings of 1/f^α dephasing detected on superconducting
  qubits" (Sec. IV C 1). Most qubits sit in the quasistatic/DC regime: "a majority of the
  IBMQP qubits suffering from correlated dephasing noise ... can be well described within
  the DC regime, namely ω_max < δω_min" (Sec. IV C 1).
- *Spatial correlation / crosstalk (quantum, extended-Markovian):* always-on qubit-qubit
  ZZ crosstalk H_XT = Σ_j σ_z^(j) Σ_{i∈C(j)} J_ij σ_z^(i) (Eq. 7); qubit–TLS ZZ coupling
  H_TLS (Eq. 8); ECR two-qubit error Hamiltonian with over-rotation ε_zx, target detuning
  β, residual x-rotation ζ, and ZZ J (Eq. 9). Sparsity finding (Sec. II C 1): "we find
  that single-qubit incoherent errors are sufficient to obtain excellent agreement with
  the decays observed in the experiments. In other words, no two-qubit dissipative terms
  are found to be necessary to explain the experiment results observed."
- *Readout/SPAM:* bit-flip channel before ideal measurement (Eq. 5); "we choose to treat
  state preparation as an effectively ideal operation and assign all SPAM errors to
  measurement errors with rates s_j" (Sec. II B 2).
- *Local dissipation:* GAD (T1 relaxation with thermal q), phase damping (T_φ), and
  bit-flip control dissipation ν acting only during x-rotations (Sec. II B 1).
- *Leakage:* NOT covered (see Q1 negative scan) [ours].

**Demonstrated scale** [paper]:
- Characterization: "Examining 39 qubits across seven devices, we comprehensively
  characterize Markovian and non-Markovian noise sources" (Sec. I); "39 qubits across
  seven devices within the Falcon and Eagle processor generations" (Sec. VII). Table II
  (Sec. IV C 3) breakdown: "Approximately 64% are found to exhibit purely Markovian
  behavior, while 26% and 10% experience correlated dephasing or control noise,
  respectively."
- Circuit families: characterization suite (SPAM M, T1, T2 Hahn echo, Ramsey, FTTPS,
  FPW, XT, CR; Sec. III B); single-qubit RB (Sec. IV A, predicted EPC within error bars);
  CPMG DD (Sec. IV C 1); FTTPS/R-FTTPS control-noise QNS (Sec. IV C 2); repeated ECR —
  "we tested 7 pairs of qubits accross [sic] four different devices" up to n = 16
  repetitions (Sec. IV D); multi-qubit DD — 1 main + 3 spectator qubits on ibm_cairo,
  "n = 1176 repetitions of XY4" to T = 83.5 µs (Sec. V A); VQE for H2 on 2 qubits of
  ibm_algiers, "∆(Ropt) ≈ 0.5%, a 7× improvement over the default model" (Sec. V B).
- Largest simultaneous quantum register in any single demonstration: 4 qubits (DD,
  Sec. V A) — plus TLS ancillas; everything else is 1–2 qubits [ours]. Table II's seven
  devices are belem, quito, lima, nairobi, jakarta, lagos, manila; figures additionally
  show algiers, auckland, hanoi, cairo, guadalupe, osaka [ours — device-name inventory].
- Sec. VI (scalability) is a *proposal/analysis*, not a demonstration: composite-channel
  reduction E_N = E_GAD ∘ E_D ∘ E_CN ∘ E_ZZ ∘ E_M (Eqs. 26–27) with noise-averaged
  dephasing/control channels built from FF overlap integrals; "Further examinations are
  required to determine if the model presented here continues to yield predictive power
  as system size increases" (Sec. VII).

## Q4 — Released code/tooling: none

**Methods paper; no released code, no repository link, no code/data-availability
statement anywhere in the text.**
- [ours] Negative scan of the full extracted text: zero occurrences of "github",
  "zenodo", "repository", "open source", "code availability", "data availability",
  "supplementary". The acknowledgments (DOE ASCR funding, Oak Ridge LCF) are followed
  directly by Appendix A with no availability section.
- The single tool mention is one uncited sentence in Appendix G (FTTPS resonances):
  "The PSD can be used alongside mezze in a stochastic noise simulation, showing
  excellent agreement with experiment." — no citation, no link, no version [paper].
  [ours] "mezze" matches JHU/APL's open-source stochastic-noise quantum-simulation
  package (github.com/JHUAPL/mezze), but the paper itself does not reference or release
  it; the noise model of this paper is not shipped as a tool.

## Limitations [paper]
- Fixed-frequency-transmon-targeted (CR/ECR gate model); "Although the noise model
  introduced here is targeted towards fixed-frequency transmons, the processes discussed
  are general" (Sec. VII).
- ECR model breaks down at large crosstalk: for one pair with "J ≈ 0.5 MHz ... the model
  was not sufficient to fit ⟨Y⟩, ⟨Z⟩" (Sec. IV D).
- Scalability beyond two-qubit demonstrations untested: "Further examinations are
  required to determine if the model presented here continues to yield predictive power
  as system size increases" (Sec. VII).
- Parameter drift/stability only preliminarily assessed over one hour on one qubit
  (Appendix I); "A thorough statistical analysis of the stability over many qubits and
  longer time windows is required" (App. I).
- No spectator-qubit local noise or spectator dissipation in the model ("our model does
  not include local noise contributions for spectator qubits, nor coupling between
  spectators and TLSs", Sec. II).

## Tags
- `[paper]` H = H_D ⊗ H_Sp ⊗ H_TLS; all factors are two-level (data qubits + spectator
  qubits + effective-qubit TLSs); temporal correlations are classical stochastic
  variables — no leakage/qutrit levels anywhere
- `[paper]` extended-Markovian trick = enlarge the LME register with ZZ-coupled two-level
  quantum DOF; stochastic tier = Gaussian WSS β(t), ε(t) with QNS-reconstructed PSDs
  (1/f^α-like, mostly DC regime)
- `[paper]` validation families: characterization suite + RB + CPMG/multi-qubit DD +
  repeated ECR + 2-qubit VQE (0.5% relative error, 7× over IBM default model); 39 qubits
  / 7 IBMQP devices characterized, ≤4 qubits per dynamics demonstration
- `[paper]` no QEC content: no syndrome/detector data, no code circuits, no decoder
- `[paper]` no released code; one uncited "mezze" simulation mention (Appendix G)
- `[ours]` all negative claims above verified by exhaustive term-scan of the full
  pdftotext extraction of arXiv v1
