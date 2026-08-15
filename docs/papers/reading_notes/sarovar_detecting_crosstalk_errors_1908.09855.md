# Full-text note (精读) — Sarovar, Proctor, Rudinger, Young, Nielsen, Blume-Kohout, "Detecting crosstalk errors in quantum information processors" (arXiv:1908.09855, Quantum 2020)

> **Provenance (2026-06-25): 精读 of the full main text** — §2-4 (crosstalk-error definition + the explicit
> crosstalk-free Markovian model + the 5 example mechanisms), §5 (why arbitrary crosstalk is hard → low-weight
> restriction), §6 (the model-free operational protocol: regions, lightweight experiment design, the
> conditional-independence analysis), §7 (2-qubit + 6-qubit simulations with explicit magnitudes). Appendices
> A-D (proofs, PC-algorithm pseudocode) skimmed. PDF→txt `outputs/papers/1908.09855.txt` (36 pp). Sandia QPL,
> Quantum 4, 321 (2020), CC-BY 4.0. The **drive/microwave-crosstalk + crosstalk-TAXONOMY + crosstalk-OBSERVABLE**
> source for the teacher-completion. Sibling crosstalk notes: `foxen_fsim..._2001.08343` (fSim coherent),
> `heinsoo_multiplexed_readout..._1801.07904` (readout), `harper_nonclifford_crosstalk_surface_2605.29514`
> (⑤a ZZ), pending Gao 2605.23385 (TLS/spectator).

## Why load-bearing [ours]
Two things, and the SECOND is the bigger gift:
1. **The canonical, hardware-agnostic crosstalk TAXONOMY** — the field-standard definition of "crosstalk-free"
   (locality + independence) and the categorization (absolute vs relative; idle / operation / detection
   crosstalk) that ORGANIZES our entire crosstalk axis and validates our enumeration is complete.
2. **The crosstalk OBSERVABLE** — a model-free, decode-independent **conditional-independence / conditional-
   mutual-information** moment between disjoint regions, with a published statistical test (G² = scaled CMI)
   and the coherent-vs-incoherent SNR behaviour. This is exactly our "moment observables certify on d3"
   methodology, GROUNDED, and its own simulations confirm our coherent→twirled→d3-gated prediction.
This is the canonical "drive/microwave crosstalk" source the prereg names, but it is a **framework + detection**
paper, not a device-magnitude paper (magnitudes are illustrative, p=ε=1e-2).

## The model — crosstalk-free definition [paper]
- **Crosstalk errors = undesired dynamics violating LOCALITY or INDEPENDENCE** (Def 1, §3). Locality: a
  circuit's physical implementation creates no correlation between disjoint qubit subsets unless an intentional
  multi-qubit op couples them. Independence: a local op's action at time t does not depend on what disjoint ops
  occur in the same layer.
- **Explicit Markovian crosstalk-free model (§4.1.3):** each layer's CPTP map factorizes as a tensor product
  of per-gate local maps (locality, Eq.3), and each gate is the SAME local map in every layer it appears
  (independence, Eq.4); prep ρ=⊗ρ_i and POVM M_i=⊗M_{j,ij} also factorize (Eq.5-6). Any violation = a crosstalk
  error.
- **absolute (locality-violating)** crosstalk = traceable to one specific layer's correlating map; **relative
  (independence-violating)** = a local op behaves differently in different layers, no single layer is "correct."
  Named subclasses: **idle crosstalk** (global-idle ≠ tensor product), **operation crosstalk** (op on region A
  changes dynamics of disjoint B — special case of relative), **detection crosstalk** (a measurement result on
  one qubit depends on another qubit's pre-measurement state).
- **Gauge caveat (§4.2):** crosstalk-freeness is a gauge-existence statement — a QIP is crosstalk-free iff
  THERE EXISTS some gauge in which Conditions 1-2 hold (gauge freedom is non-local; relevant to our
  gauge/cut-space band-widening axis).

## The 5 example mechanisms (§4.3) [paper] — these ARE the crosstalk taxonomy items
1. **Pulse spillover** (= drive/microwave crosstalk): an Xπ on A spills a small X rotation onto idle B →
   violates **independence** (B's idle map depends on A's op). The most-discussed form; this is the drive-
   crosstalk mechanism for our teacher.
2. **Always-on Hamiltonian** (XX): idle qubits feel an unwanted XX → entangling idle → violates **locality**.
   (≈ our ⑤a always-on ZZ, X-basis analogue.)
3. **Correlated stochastic errors from a common cause** (Fig 2): both qubits couple to a common white-noise-
   fluctuating field → correlated weight-2 dephasing / ZZ during idle → violates **locality**, EVEN WITH NO
   DIRECT QUBIT-QUBIT COUPLING. (= the grounding for our ⑤a-spatial + ⑤b-temporal common-cause picture; a
   *constant* field gives only local rotations and is NOT crosstalk.)
4. **Detection (readout) crosstalk**: measuring A's result depends on B's state (scattered-photon flip) →
   POVM not a tensor product → violates **locality**. (= the Heinsoo readout form.)
5. **Correlated state preparation**: common control-field noise correlates the prepared state → locality
   violated only after averaging over inits.

## Key numbers [paper] — the simulations (§7), and the coherent-vs-incoherent smoking gun
All simulations use elementary {Xπ/2, Yπ/2, I}, local depolarizing plocal, random RB-like subcircuits, the
G²/PC analysis; magnitudes are ILLUSTRATIVE not device-measured.
- **Operation crosstalk 1 (classical / control-line):** Xπ/2 on q0 → depolarizing D_p on q1 (Eq.13),
  **p=1e-2, plocal=1e-2**, L=30, Ncircs=10, Nrep=1e4 (Nexp=100). Detected; edge S0→R1.
- **Operation crosstalk 2 (COHERENT Z⊗Z Hamiltonian):** Xπ/2⊗I → exp[−i/2(π/2 X⊗I + ε Z⊗Z)] (Eq.14),
  **ε=2e-2**, L=30, Ncircs=10, **Nrep=1e5** (10× the stochastic case). **THE LOAD-BEARING SENTENCE (p.22):
  "the coherent crosstalk error shows up at ∼ε² in the measurement probabilities since we are using random
  gate sequences, and this is why more samples are required to detect this crosstalk error."** Conditional
  dependence appears between RESULTS R0-R1 (not just S→R), no clear causal direction.
- **Detection (readout) crosstalk:** if q0 reads 1, q1's readout flips w.p. **pm=1e-2** (Eq. for E10/E11),
  L=10, Ncircs=20, Nrep=1e5 (Nexp=400). "Effects do not build up over a gate sequence, thus only impact the
  outcome probabilities weakly" → needs larger Nrep+Ncircs. Edge R0-R1 (incoherent classical correlation).
- **6-qubit ladder:** vertical-neighbour operation crosstalk detected with **only 300 distinct experiments**
  (linear-in-n burden). Protocol cost = **Õ(n³)** general, **Õ(n²)** under local connectivity.

## The observable, precisely (§6.4) [paper]
- **Def 2 (model-free crosstalk-free):** region r_i is crosstalk-free iff `P(R_ri | S_ri, T) = P(R_ri | S_ri)`
  for any `T ⊆ Ω\{R_ri,S_ri}` (Eq.9) — the measurement results on r_i depend only on r_i's settings,
  CONDITIONALLY independent of all other regions' settings/results. (Conditional, not marginal, indep —
  robust to confounded settings.)
- **Test:** the **G² log-likelihood-ratio CI test** (Eq.11), `G²(i,j|A) = 2Σ n log(...)`, asymptotically
  χ² with df=(|Xi|−1)(|Xj|−1)|XA|; it is a **scaled empirical conditional mutual information** I(Xi;Xj|A).
- **Structure discovery:** the **PC algorithm** (constraint-based, Spirtes-Glymour) builds the graph SKELETON
  by iterated CI tests (edge-orientation step DROPPED — they want dependence, not causation). Quantify each
  crosstalk edge by **max-over-(i,j) TVD** of the conditional outcome distributions (Eq.12).
- **Explicitly NOT a causal claim** (§6.4): "we are not making claims about causality… simply using causal-
  inference tools to assess conditional-independence." (Note for us: this is the *detection* reading; our twin
  goes further to an SCM/do() — Sarovar is the conditional-indep observable, not the interventional layer.)

## Limitations / what does NOT apply [paper→ours]
- **Magnitudes are illustrative** (p=ε=pm=1e-2). Sarovar gives NO device-measured drive-crosstalk rate; real
  drive/microwave-crosstalk magnitude must come from a device source (Foxen parallel-CZ stray coupling; Willow
  2408.13687 stray-ZZ) → BRACKET, do not freeze.
- **Detection is not characterization** (§8): max TVD is NOT a physical error rate (§7.1.4 — it is sample-
  dependent, can be non-monotone in ε); the protocol localizes WHICH regions, not HOW the channel acts.
- **Faithfulness failure (§6.5, Factor 3 — the critical caveat for OUR moment observable):** a pairwise CI
  test (and PC) FAILS to detect crosstalk when the outcome distribution is UNFAITHFUL to the dependence:
  pairwise-independent-but-jointly-dependent (X3=X1⊕X2), multiparty data-hiding states, or high-weight /
  π/2-rotation / fine-tuned-cancelling crosstalk → "no edge" despite real correlation. They argue these are
  "extremely artificial" / high-weight and not seen in physical models, BUT this is the exact failure mode a
  conditional-/marginal-moment certify check must guard against (cf. `kam... §IV.C`: 2-point autocorrelation
  insufficient; cf. our prevent-toy "could this check fail?" discipline `[[feedback-scrutinize-vacuous-checks]]`).
- Only weight ≤2 regions tested → no guarantee on weight-≥4 crosstalk; only Markovian (drift/non-Markov must
  be excluded first, else confounded — randomize/rasterize circuits in time).

## Relevance to the teacher (crosstalk form: drive/microwave + the taxonomy + the observable) [ours]
- **Teacher recipe (drive/pulse-spillover crosstalk):** when an op acts on region A, apply to spectator B
  (i) a small coherent over-rotation (spillover unitary, e.g. `exp(−iδ X_B)` or the Z⊗Z of Eq.14) AND/OR
  (ii) its twirled effective stochastic残差 (a depolarizing/dephasing kick D_p on B conditioned on A's op,
  Eq.13). Reuse the ⑤a two-site machinery (`mechanisms/teachers.py:zz_coupling_kraus` /
  `correlated_dephasing_kraus`); the operation-conditioning is the new bit (independence-violation = a
  context-dependent local map). Magnitude **bracketed** (illustrative 1e-2; real ≲1e-3 drive spillover) — SWEEP.
- **THE COHERENT-vs-INCOHERENT VERDICT IS CONFIRMED BY THIS PAPER'S OWN SIMULATIONS.** Sarovar's coherent
  Z⊗Z crosstalk under **random (twirling) circuits manifests only at O(ε²) and needs 10× the shots**, while
  the stochastic depolarizing operation-crosstalk and the incoherent readout-detection crosstalk show at first
  order. This is precisely our `[[project-axisA-teacher-ws1-ws2]]` certifiability map: **coherent drive
  crosstalk → syndrome-TWIRLED → suppressed / d3-GATED** (same class as ②/⑤a-coherent/fSim), **incoherent
  (stochastic operation + detection) crosstalk → first-order → CERTIFIABLE moment axis**. The EMERGING PATTERN
  (coherent→twirled→d3-gated; incoherent→certifiable moment) now has a third independent confirmation in the
  crosstalk literature itself.
- **The bigger gift — the OBSERVABLE grounds our certify methodology.** The conditional-independence /
  conditional-mutual-information moment (G² test, max-TVD edge) is a published, field-standard, decode-
  INDEPENDENT crosstalk witness. It is the literature anchor for our `audit/certify` moment-check (the
  ⑤a spatial_corr edge-excess, the readout-correlation moment, the drive operation-crosstalk witness): use
  **conditional MI / TVD between a witness region's syndrome outcomes and a neighbour region's settings/
  outcomes** as the certify statistic, and carry the **faithfulness caveat** (§6.5) as a declared limitation
  (a pairwise/2-point moment can MISS XOR-type / data-hiding / high-weight crosstalk — match against an
  independent higher-order check, never a single pairwise CI test).
- **SCM/do() connection (for the UQ layer, [[project-uq-novelty-verdict]]):** Sarovar deliberately stops at
  conditional-independence detection and disclaims causality. Our twin's novelty hinge is exactly the step
  Sarovar declines — going from the observational conditional-indep witness to an **interventional SCM**
  (do() on the teacher). Useful framing: Sarovar = the observational crosstalk OBSERVABLE; the twin = the
  interventional model that the simulator-teacher's known-truth do() validates.
- **Epistemic classes for the prereg:**
  - drive coherent-spillover rotation = **(c)/bounded-simplification**: coherent → twirled → d3-gated, bracketed
    ≲1e-3, NOT inflated (Sarovar's own ε² SNR is the grounding for the suppression).
  - drive stochastic operation-crosstalk (twirled residual D_p on spectator) = **(b) prediction band**: a
    first-order, certifiable conditional-MI/TVD moment that an iid-Pauli learner misses; bracketed magnitude.
  - the conditional-independence/CMI observable + G²/max-TVD statistic = **(a)-grade methodology import** (a
    field-standard test, used as the certify statistic), carrying the **(c) faithfulness gate** caveat.

## Trust [ours]
Full-text 精读: the locality/independence definitions (Def 1, §3), the explicit crosstalk-free model (Eq.3-6),
the 5 examples (§4.3), the model-free Def 2 + G² CI test (Eq.9, Eq.11), the PC-skeleton + max-TVD quantifier
(Eq.12), and ALL the §7 simulation magnitudes (p=ε=pm=1e-2, the ε² / 10×-Nrep coherent finding, the 300-expt
6-qubit demo). Appendices (proofs A-B, PC pseudocode C-D) skimmed. The "coherent→twirled→d3-gated CONFIRMED by
their own ε² simulation" and the "conditional-MI observable grounds our certify" verdicts are [ours], grounded
in p.22 + §6.4 read directly. No device-measured drive magnitude exists here — that bracket is flagged.
