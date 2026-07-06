# Full-text note — Manabe, Suzuki & Darmawan, Efficient Simulation of Leakage Errors in QEC Codes Using Tensor Network Methods

> **Provenance.** Full-text read (all 15 pages incl. Appendix A and the appended
> Kraus-sampling paragraph, plus every figure) of the cached PDF
> `docs/papers/leakage_tensor_network_simulation_2308.08186.pdf`. The PDF ships with a
> permissions-only encryption layer; it was decrypted with PyMuPDF
> (`encryption=PDF_ENCRYPT_NONE`) and read via the extracted text + per-page raster
> renders of the figure pages (Figs. 1, 3, 5–8, 12 inspected visually). Title:
> *"Efficient Simulation of Leakage Errors in Quantum Error Correcting Codes Using
> Tensor Network Methods."* arXiv:2308.08186v2 [quant-ph], 21 Jan 2025.
> **Role in our program: this paper's qutrit-MPS IS the scalable faithful GENERATOR —
> the approximation-free, twirl-free forward simulator that emits the leakage record
> {det,obs} at large d, and whose one bond-truncation approximation we bound against
> the exact qutrit-DM oracle. Core `forward/scalable` simulator infrastructure.**

> **[ours] reframed 2026-07-06** — the decoder-oriented framing below ("sim-only
> teacher / decoding headroom above MWPM") is SUPERSEDED by the
> simulator-forward-generation framing: validity = faithfulness vs an independent
> qutrit oracle + anti-toy discriminability of the record from a matched Markov/DEM
> null; decoder/LER = downstream use, not validity. This paper's qutrit-MPS = the
> scalable faithful generator/reference. See
> docs/twin_validation/HANDOFF_static_simulator_notion2_2026-07-06.md.

## Metadata

- **Authors.** Hidetaka Manabe (Osaka Univ., Graduate School of Engineering Science);
  Yasunari Suzuki (NTT Computer and Data Science Laboratories; JST PRESTO);
  Andrew S. Darmawan (YITP, Kyoto Univ.; JST PRESTO).
- **Status.** arXiv:2308.08186v2, 21 Jan 2025 (preprint; v1 Aug 2023). Not a
  peer-reviewed journal version in this cache.
- **Domain / type.** QEC / fault tolerance; **simulation methodology** — exact
  (non-Pauli, non-twirled) leakage simulation on QEC codes via Matrix Product States
  (MPS). Darmawan is the through-line to the project's existing TN line
  (`darmawan_poulin_*`, `darmawan_decoder_adaptation_local_noise_2403.08706`).
- **Code/tools.** Implemented on Google's `TensorNetwork` Python library [68].
  Hardware used: one Intel Xeon Platinum 9242 node, 96 threads, CPU-only. Each plotted
  point averages **10 000 samples** (a few thousand for some figures).

## TL;DR

The paper gives a **scalable, approximation-free (no Pauli/twirl) simulator of
leakage errors in QEC codes** by treating each physical element as a **qutrit**
(levels |0⟩,|1⟩,|2⟩) and representing the full many-qutrit pure state of the QEC
circuit — data **and** ancilla qubits together — as a **Matrix Product State (MPS)**.
The decisive physical observation is that **repetitive stabilizer measurement keeps the
QEC state low-entanglement** (it repeatedly projects the system back toward a product /
locally-corrected state), so the bipartite entanglement obeys an **area law** and a
**small, _bounded_ bond dimension χ suffices** even over many rounds and hundreds of
qutrits. This is exactly the regime where MPS is efficient and exact state-vector
simulation (≈ petabytes for 30 qutrits, p.3) is impossible.

The method is a **pure-state stochastic-trajectory** simulator: unitaries / CPTP Kraus
operators / projective measurements are applied as local MPS tensor updates; bond
truncation via SVD is controlled by a **truncation-error threshold** (the 2-norm of the
discarded singular values), set to **10⁻⁶ (repetition code) / 10⁻⁴ (thin surface
code)**. CPTP (non-unitary) noise — amplitude damping + thermal excitation — is handled
by **Kraus-operator sampling** with probability `p_i = Tr(K_i|ψ⟩⟨ψ|K_i†)` (Eq. A9), so
each trajectory stays a pure MPS. The pipeline **does produce syndrome samples**: it
simulates each round's ancilla measurement, feeds the syndrome history to **MWPM**, and
records a logical-error event — so the per-shot output is precisely a
`(syndrome-history, logical-flip)` record, i.e. the faithful `{det, obs}` record our
simulator must GENERATE (the MWPM decode step is downstream product, not part of that
record contract).

Headline scientific findings: (i) the required χ stays small and **saturates / is
constant in d** at large round count (area law, Fig. 6) → scalable to a few hundred
qutrits; (ii) the **stochastic (General-Twirling-Approximation) surrogate of coherent
leakage can over-predict the logical error rate by >3×** (Fig. 8), so leakage/seepage
rates alone are **not** sufficient descriptors; (iii) leakage-removal strategy choice
matters most at **large code distance** and differs sharply by leakage type, including
a **threshold-disappearance / reversal** at small bath coupling and large d (Figs.
10–12).

## Main Contribution + Core Method (full technical detail)

### C0. The object: a qutrit MPS for the whole QEC circuit

Every physical site is a **3-level system** (qutrit), so leakage |1⟩→|2⟩ and seepage
|2⟩→{|0⟩,|1⟩} are represented **natively**, not Pauli-twirled away. The simulator
includes **both data and ancilla qubits inside one MPS** (Sec. IV.A, p.5–6):

- **1D repetition code, distance d:** data and ancilla alternate on a line → **2d−1
  sites** total. Logical |0⟩/|1⟩ (with ancillas) is a product state → exactly an MPS
  with **χ = 1** (p.6).
- **3×d thin surface code:** **6d−1 qubits**; the MPS is routed **snake-like** through
  the 2D layout (Fig. 3a). The logical |+⟩ is a low-entanglement state representable at
  **maximum χ = 4** (p.6). Because the snake makes some two-qubit gates act on
  MPS-distant sites, the gate must be applied as an **MPO of length up to 6** (Fig.
  3b), which raises cost. Scaling note (p.6): 5×d and 7×d surface codes need only
  χ = 8, 16 to hold the logical state, but their MPO lengths (10, 14) make noise spread
  over many tensors and inflate cost.

**This is the qutrit/multi-level handling the task asks about: the leakage level is a
third physical index on every MPS tensor; nothing is projected onto the qubit
subspace.** The price of "true 3-level" is exactly that the physical bond dimension
per site is 3 (vs 2), and that CPTP maps need Kraus sampling (below).

### C1. The leakage noise model (Sec. II) — what gets simulated, as channels

The noise is **phenomenological but non-Pauli and coherence-preserving**, tuned to
superconducting qutrits. Five mechanisms:

1. **Single-qubit (control / fast-pulse) leakage (Sec. II.A, Eqs. 1–5).** A coherent
   over-rotation that couples qubit and leaked levels:
   `U = U_z(φ_i)·R02(θ,λ_i)·R12(θ,λ_i)`, with
   `R02 = U02(θ,λ_i) ⊕ I1`, `R12 = U12(θ,λ_i) ⊕ I0`,
   `U(θ,λ_i) = e^{-iθ/2} exp(iθ/2(cos λ_i X + sin λ_i Y))`, and a leaked-level phase
   `U_z(φ_i) = diag(1,1,e^{iφ_i})`. **θ = rotation-noise strength** (the control-leakage
   knob); **λ_i, φ_i = per-qubit random phases** drawn from [0,2π). Applied after each
   CZ.
2. **Controlled-phase (CZ) gate leakage (Sec. II.B, Eq. 6).** A 9×9 (qutrit⊗qutrit)
   `CZ_noisy`: acts ideally on the qubit subspace, but **adds a phase i (π/2) when the
   control is in |2⟩** (chosen as the intermediate between the 0 and π shifts observed
   in Miao et al. [6]). Noisy CNOT = `(I⊗H)·CZ_noisy·(I⊗H)` with a qutrit H (Eq. 7).
3. **Leakage spreading (Sec. II.B).** A phenomenological coherent **Y-rotation by
   θ_spread** in the subspaces {|02⟩,|22⟩},{|12⟩,|22⟩},{|20⟩,|22⟩},{|21⟩,|22⟩},
   applied after CZ — a qubit-subspace state coherently rotates into leakage **when its
   neighbor is leaked**. This is the "leakage is contagious via two-qubit gates" effect
   [6, 14].
4. **Measurement (Sec. II.C, Eqs. 8–9).** A CP instrument:
   `E0(ρ) = Π0 ρ Π0 + p Π2 ρ Π2`, `E1(ρ) = Π1 ρ Π1 + (1−p) Π2 ρ Π2`, with **p = 0.5**
   (a leaked qutrit is read out as 0 or 1 with equal probability), `Π_i = |i⟩⟨i|`.
   Measurement-induced leakage is **neglected** here (could be folded into gate leakage;
   they focus on CZ + thermal as the dominant sources, p.3).
5. **Idling / thermal noise (Sec. II.D, Eq. 10).** Amplitude damping + thermal
   excitation from a harmonic-oscillator–bath Lindbladian
   `ρ̇ = γ(N+1)(aρa† − ½{a†a,ρ}) + γN(a†ρa − ½{aa†,ρ})`,
   with `N = (e^{ℏω/k_BT} − 1)⁻¹`, coupling γ, effective temperature `k_BT/ℏω`. They
   **integrate this over a gate time and cut off higher levels to get a CPTP Kraus map**,
   applied to **all qubits at the start of each round**. Parameters (p.3): qubit
   frequency 10 GHz, `k_BT/ℏω := αT` with `α ≈ 13.1 K⁻¹`, gate time τ = 1.0 µs, γ in MHz,
   T in mK.

**Key point for us:** items 1–3 and 5 are precisely the **non-Pauli / coherent**
signals (T1/T2-type thermal + coherent leakage + spreading) that a Pauli decoder cannot
see; the simulator keeps the coherence (no twirl), which is the whole motivation.

### C2. MPS circuit simulation + bond truncation (Sec. III, Appendix A)

State (Eq. 11): `|ψ⟩ = Σ_{s_i} Σ_{α_i} A^{[1]s1}_{α1} A^{[2]s2}_{α1α2} ⋯ A^{[n]sn}_{α_{n-1}} |s1…sn⟩`,
physical indices `s_i` (dim 3), virtual/bond indices `α_i` (dim χ). An MPS with bond
dimension χ represents states with **bipartite entanglement entropy ≤ log₂ χ** across
any cut (p.4) — this is the exact statement of the approximation's expressive ceiling.

Tensor updates (Appendix A, Eqs. A1–A8):

- **Single-qubit gate / sampled Kraus / projector** at site i: contract into the local
  tensor, `A^{[i]s_i} ← Σ_{s'_i} M^{s_i}_{s'_i} A^{[i]s'_i}` (Eq. A1) — **no bond growth**.
- **Two-qubit gate** on neighbors i,j: write the gate as a 2-site **MPO** via SVD (Eq.
  A2); for **non-neighboring** i<j, insert identity "pass-through" MPO tensors
  `M^{[l]}_{α_{l-1}α_l} = δ_{α_{l-1},α_l} δ_{s_l,s'_l}` on all intermediate sites (Eq.
  A3) — this is how the snake's long-range gates are realized.
- **Canonical update / truncation (the core step).** Put the MPS in **canonical form**:
  all tensors are isometries (Eqs. A4–A5) except one **"top tensor"** at site k; isometry
  is restored by successive SVDs. To apply a 2-qubit gate, move the top tensor to site i,
  apply the MPO site-by-site, and at each adjacent pair contract
  `A^{[l,l+1]}` then **SVD-split** it `= Σ_{α_l} U S V†` (Eq. A6). **Bond truncation =
  discarding the small singular values of S**, then re-absorbing
  `A^{[l]} = U`, `A^{[l+1]} = S V†` (Eqs. A7–A8). Repeat to site j. This simultaneously
  applies the gate and caps the bond dimension.

**The approximation and its knob.** The *only* approximation is the SVD truncation. It
is controlled **not by a fixed χ but by a truncation-error tolerance**: the
**2-norm of the vector of discarded singular values** at each step must stay below a
threshold ε (Sec. V.A, p.7). They set **ε = 10⁻⁶ (repetition code)** and **ε = 10⁻⁴
(thin surface code)**, and **"confirmed [it] is sufficient to accurately calculate the
logical error rate in the parameter regions studied."** χ is then chosen **dynamically**
per step to meet ε. Cost: each truncation/SVD is the dominant expense; for d ≥ 5 thin
surface codes the **SVD is the explicit bottleneck**, motivating GPU/cluster SVD (p.10,
Sec. V.C).

### C3. Non-unitary (CPTP) noise via Kraus sampling — keeps trajectories pure (Appendix A, Eq. A9)

This is the mechanism that lets a **pure-state MPS** represent **dissipative** thermal
noise (and the measurement instrument). For a CPTP map with Kraus set {K_i}, **sample
one Kraus operator** with probability

> `p_i = Tr(K_i |ψ⟩⟨ψ| K_i†)`   (Eq. A9)

(efficiently computable from the MPS), then apply the selected K_i as a single-qubit
gate (with renormalization). Projective measurements are sampled the same way. Averaging
over **10⁴ trajectories** reconstructs the channel-averaged logical error rate. So the
simulator is a **quantum-trajectory / stochastic-unraveling MPS**, not a density-matrix
MPO — this is why it scales (one pure MPS, not a doubled-wire mixed state).

### C4. The QEC pipeline + leakage-removal strategies (Sec. IV)

- **Repetition code (Fig. 2):** prepare product |0…0⟩/|1…1⟩, run **d rounds** of
  syndrome extraction (couple two data qubits to one ancilla, measure ancilla), then
  measure all data qubits; **decode with MWPM** [24, 65]; logical error rate =
  P(decoding failure).
- **Thin surface code (Fig. 3):** 3×d, decoded for **logical Z (distance d, vertical
  chain) and logical X (fixed minimum length → X-error rate _grows_ with d)**. d is the
  **Z-distance**.
- **Three leakage-removal strategies** (Sec. IV.B), simulated as channels:
  1. **No reset (Eq. 12):** `M_noreset(ρ) = (⟨0|ρ|0⟩+⟨1|ρ|1⟩)|0⟩⟨0| + ⟨2|ρ|2⟩|2⟩⟨2|` —
     leaked ancilla stays leaked.
  2. **Multi-level reset (MLR):** `M_MLR(ρ) = |0⟩⟨0|` — ancilla forced to |0⟩ every round
     (removes ancilla leakage, **not data** leakage).
  3. **DQLR (Data-Qubit Leakage Removal, Fig. 4):** after MLR, apply a **LeakageISWAP**
     [6] between data and ancilla acting on the {|11⟩,|20⟩} subspace, converting |02⟩→|11⟩
     (moves data leakage to ancilla), then MLR again. Most effective.

## Key Results (figures + tables)

> The paper has **no numbered tables**; all results are figures (vector graphics — the
> per-figure numbers below are read off the rendered plots and captions).

- **Fig. 1 (p.4).** Diagram of the MPS (a) and the **canonical-update SVD truncation**
  (b): top tensor (square) vs isometries (triangles), MPO applied site-by-site from site
  i with SVD truncation — the algorithm picture for C2.
- **Fig. 2 / Fig. 3 (p.5).** Repetition-code circuit; thin-surface-code snake layout
  (data = white, X-ancilla = orange, Z-ancilla = blue) and the length-≤6 MPO.
- **Fig. 5 (p.7) — bond dimension, repetition code, d = 99, 99 rounds, θ_spread = 0.3π.**
  Average χ to hold ε = 10⁻⁶ across (θ, γ, T, strategy). χ is **small throughout**
  (single digits to a few tens); largest in the **No-reset, low-strategy** corner.
  Sample numeric labels (avg χ): No-reset T=10 ranges ~7.7–64.8; **DQLR collapses χ to
  ~3.7–5.7** (leakage removal ⇒ less entanglement ⇒ smaller χ). χ **rises with the
  coherent component**, **falls with stronger leakage removal**.
- **Fig. 6 (p.7) — χ vs round, several d (7…99).** χ grows ~**linearly at early rounds
  then saturates**; at large round count χ is **constant in d** (except finite-size for
  d ≲ 50). The paper reads this as an **area law** (constant entanglement in 1D) →
  **scalability**, in contrast to a generic depth-n brickwork circuit needing
  exponential χ.
- **Fig. 7 (p.8) — bond dimension, 3×7 surface code, 7 rounds, ε = 10⁻⁴.** Same trend;
  avg χ ~9–21; **not yet saturated** (few rounds); surface sim is costlier than the
  repetition code.
- **Fig. 8 (p.8) — EXACT vs GTA (the accuracy/over-prediction result).** Logical error
  rate vs γ for d = 19, T = 10, θ = 0.1π, three strategies; **solid = exact MPS, dashed
  = General-Twirling-Approximation (incoherent surrogate)**. The GTA channel is built
  (Eqs. 16–20) from leakage rate L1 and seepage rate L2 (Eqs. 13–15) plus a Pauli-twirl
  of the in-subspace unitary. **GTA over-predicts the logical error rate substantially —
  "by more than a factor of three in the MLR case."** ⇒ leakage/seepage rates are
  **insufficient** summaries; coherence matters.
- **Figs. 9–11 (p.9–10) — repetition-code leakage physics.** Fig. 9: LER vs γ across T
  and θ_spread (d = 49, θ = 0.05π) — high-T thermal excitation and leakage spreading both
  worsen LER; **DQLR is nearly insensitive to spreading**. Fig. 10: LER vs γ for many d
  (T = 10, θ = 0.05π, θ_spread = 0.3π) — at large d and **small γ the LER _sharply rises_
  as γ → 0** (no/weak amplitude damping ⇒ leaked states persist and spread, destroying
  the logical state); a **non-monotone, large-d-only** effect invisible to small-scale
  sims. Fig. 11: LER vs over-rotation θ for many d (T = 10) at γ = 0 and γ = 0.1; pure
  control leakage worsens with system size; **DQLR very effective**; for DQLR at d = 49,
  99 **exactly zero logical errors** were detected.
- **Fig. 12 (p.11) — thin surface code, 3×d.** Logical **Z** error rate `P_ZL` vs γ
  (No-reset, MLR; θ = 0.05π, 0.1π; T = 10, θ_spread = 0; no spreading, only No-reset/MLR
  for cost). Same trends as the repetition code, including a **reversal where LER grows
  with d at small γ → threshold disappears**; the **inset shows logical X rate `P_XL`
  increasing with d** (as predicted for the thin code). They expect the same in full
  d×d surface codes.

**Bottom line of the results:** the entanglement really is small and bounded (Figs.
5–7) so the method is **accurate _and_ scalable** over many rounds and hundreds of
qutrits, and the exact-vs-twirl gap (Fig. 8) is the scientific payoff — **non-Pauli
coherent leakage is decoding-relevant and is mis-estimated by stochastic surrogates.**

## **Useful for Our Project** (the load-bearing section)

Our program builds the **error-coupling SIMULATOR** — a faithful FORWARD GENERATOR that
emits realistic-noise surface-code records **{det,obs}** with **non-Pauli** signal (T1/T2,
leakage |1⟩→|2⟩ + seepage, soft readout). **Leakage is the strongest genuinely
non-Markovian, NON-DEM-reducible notion-2 SOURCE**: it persists and hops, imprinting a
correlated-detection tail / long-range off-diagonal `p_ij` structure on the record that a
Stim-DEM / Markov-k null cannot forge — so it carries **anti-toy legitimacy** (the modeled
feature is distinguishable from a matched CP-divisible / best-Pauli-DEM null). But **true
leakage needs a 3-level sim that does not scale** on a density matrix, so we need a
**scalable faithful generator whose one approximation (MPS bond truncation) we can BOUND
vs an exact qutrit reference**. This paper's qutrit-MPS is that generator; it is a direct
hit on every clause. Validity here = (i) FAITHFULNESS (generated record matches the
independent qutrit-DM oracle) + (ii) ANTI-TOY LEGITIMACY (record distinguishable from a
matched Markov/DEM null); the decoder and LER are the simulator's downstream product, **not**
in the validity chain (memory `feedback-simulator-not-decoder`).

**1. Is this the scalable faithful generator for our simulator? Yes — it is essentially
the reference design for `forward/scalable`.**
- **Qutrit-native, no twirl (Sec. II, C0):** leakage and seepage are physical |2⟩
  transitions, exactly the dominant non-Pauli signal we want. Their five channels (Eqs.
  1–12) are a ready-made, citable, superconducting-tuned leakage model — control leakage,
  CZ-conditioned phase, **leakage spreading** (the contagion our Pauli teacher cannot
  produce), soft readout (Eqs. 8–9, **p = 0.5** is literally "soft/erased readout on
  leakage"), and **thermal T1/T2 via a Lindblad→Kraus map** (Eq. 10) — and our project
  already owns canonical T1/T2 Kraus channels, so item 5 plugs straight into our
  `forward/channels`.
- **Scalability mechanism (Sec. III, Figs. 5–7):** the MPS + dynamic-χ trajectory method
  scales to **a few hundred qutrits over ~100 rounds on one CPU node** *because* QEC
  states are area-law. This is the concrete route past the density-matrix wall noted in
  our own README (`forward/exact` explodes past ~15 qubits) — **the qutrit MPS-trajectory
  is the scalable faithful generator for `forward/scalable`** on the leakage axis
  specifically. Caveat: demonstrated for **1D / quasi-1D (3×d) codes**; full 2D d×d needs
  PEPS/isoTNS (their own Sec. VI / W-list).
- **Trajectory architecture (Eq. A9):** Kraus sampling keeps each shot a **pure MPS**, so
  dissipative T1/T2 and the readout instrument cost the same as unitaries — this is the
  design pattern our generator adopts (stochastic unraveling, not a doubled-wire MPO), and
  it is what makes the faithful many-round record emission feasible.

**2. How do they bound the approximation error vs exact? Via a per-step truncation-error
tolerance — but note the bound is _controlled_, not _certified absolute_.**
- The only approximation is SVD bond truncation. They control it by the **2-norm of the
  discarded singular values per truncation ≤ ε**, with **ε = 10⁻⁶ (rep) / 10⁻⁴
  (surface)** (Sec. V.A, p.7; Appendix A). The per-cut **discarded weight is the local
  fidelity-loss proxy** — a quantity our engine can log every step as a running
  truncation-error budget (this is the standard MPS error monitor).
- **Convergence knob:** because χ is chosen dynamically to meet ε, **decreasing ε → larger
  χ → systematically higher fidelity** (Sec. III.B, p.5: "fidelity can be improved
  systematically by choosing larger χ"). The **validation they actually do** is an
  **ε-refinement / self-consistency check** — "confirmed [10⁻⁶/10⁻⁴] is sufficient to
  accurately calculate the LER in the parameter regions studied" (p.7) — i.e. they
  **lower ε until the LER stops moving**, the de-facto exact reference being the
  small-χ-converged MPS itself (plus the χ = 1, 4 _exact_ noiseless logical states, p.6).
  **What they do _not_ provide is an a-priori, rigorous global error bound as a function
  of ε.** So for us the honest framing is: **error-_controlled_ (refine-to-convergence +
  per-step discarded-weight budget), with an _independent_ exact reference needed for a
  true bound on the GENERATED RECORD.** Per `docs/FAITHFULNESS_PROTOCOL.md` this bond
  truncation is a declared, bounded simplification (its `MpsTruncationLedger` entry). For
  small systems the independent oracle exists in our own tree: **the exact qutrit
  density-matrix backend `src/error_coupling_simulator/carrier/exact/qutrit_dm.py`
  (≤ 9 qutrit = one d3 tile; ≤ ~15 qutrit generally)** is the **exact oracle that certifies
  the generated record — the record distribution over {det,obs}, not merely the LER — and
  pins the discarded-weight ↔ record-error relation** before trusting the MPS at large d.
  That oracle cross-check (exact qutrit-DM vs MPS on a d3 tile) is the analogue of our
  existing fused-Kraus correctness oracle and is the rigorous, area-law-backed version of
  their self-consistency check; the area-law argument (Figs. 5–7) is what makes the
  truncation controllably small in the first place.
- This matches our metric/epistemic discipline: the truncation tolerance is a **heuristic
  gate (class c)**; only the exact qutrit-DM cross-check at small d is **class (a) exact**,
  and it is what earns the record's FAITHFULNESS claim.

**3. Does it emit the faithful record {det,obs}? Yes — directly, and that is the whole
output contract of the generator.** Each trajectory simulates every round's **ancilla
measurement** (Eqs. 8–9 sampled via A9) and accumulates the **multi-round syndrome
history**; sampling the leaked-state readout (Eqs. 8–9) is itself a physical part of the
faithful record. Their pipeline then runs **MWPM** and records a **logical-flip** event
(Sec. IV.A; LER = P(MWPM failure)) — but for us **that decode step is downstream use, not
the generator's job**: the generator emits the **detector record `det` (syndrome history)
+ observable `obs` (logical label)** shot by shot, an isolation-clean artifact where the
`obs` label is an **evaluator-side ground-truth label** (isolation contract — never fed to
any learner). So adopting their engine gives us the faithful record-generation loop
directly; the LER through **our frozen decoder** is then just one downstream product
scored off those records.

**4. Anti-toy legitimacy of the leakage source, pre-validated (this is a legitimacy
result, not a decoding-headroom result).** Fig. 8's **>3× GTA over-prediction** and the
paper's explicit conclusion that **"leakage and seepage rates do not fully capture the
impact of leakage"** is an independent, citable demonstration that **a Pauli/twirl
(effectively DEM-reducible) model of leakage cannot reproduce the leakage record** — i.e.
the leakage feature is genuinely **not forgeable by a matched Markov/best-Pauli-DEM null**,
which is exactly the ANTI-TOY LEGITIMACY criterion the simulator must clear (a modeled
feature distinguishable from a matched CP-divisible / DEM null). The record-level analogue
of Fig. 8 for us is a **correlated-detection tail / long-range off-diagonal `p_ij`** the
null cannot forge; the >3× LER gap is the paper's coarse (decoder-side) shadow of that
record-level distinguishability, and its **over**-prediction sign warns the twirl surrogate
is pessimistic. Darmawan is a co-author and the project already carries his TN line, so
this slots cleanly into the existing citation web (`darmawan_*`, `ferris_poulin_*`,
`harper_nonclifford_crosstalk_surface_2605.29514`).

**5. Concrete adoption checklist (for the scalable leakage GENERATOR build).**
- Reuse **Eqs. 1–12 + Eq. 10** as the leakage channel set (control / CZ-phase / spreading
  / soft-readout / thermal-Kraus); cite this paper for the model.
- Generator: **qutrit MPS-trajectory** with **dynamic-χ to a truncation-error ε**, Kraus
  sampling (Eq. A9), living in `forward/scalable`. Start at **1D rep + 3×d thin surface**
  (their validated regime), treat full d×d as future PEPS/isoTNS work.
- **Bound the truncation error our way (this earns FAITHFULNESS):** (i) log per-step
  discarded weight as a declared budget (the `MpsTruncationLedger`, per
  `docs/FAITHFULNESS_PROTOCOL.md`); (ii) sweep ε and confirm the generated record
  converges (their self-consistency check); (iii) **certify the RECORD against the exact
  qutrit-DM oracle `src/error_coupling_simulator/carrier/exact/qutrit_dm.py` at d = 3 /
  ≤ 9–15 qutrits** — the independent exact reference they lack and we have.
- Emit the faithful `{det, obs}` record shots (isolation-clean, `obs` = evaluator-side
  label). Establish validity by (a) faithfulness vs the qutrit-DM oracle and (b) anti-toy
  discriminability of the record from a matched Markov-k / best-Pauli-DEM null. **LER /
  scaling through our frozen decoder is a downstream PRODUCT the record must reproduce
  (`docs/METRICS.md`), NOT part of the validity chain.**
- **GPU:** they are CPU-bound and call out **SVD as the d ≥ 5 bottleneck** (p.10) → our
  GPU-only mandate is the right move; batched/GPU SVD + CUDA-graph trajectory batching is
  the obvious win (consistent with our launch-bound-not-CPU policy).

## Limitations / what does NOT apply

- **W1 — 1D / quasi-1D only.** MPS is efficient here *because* the repetition code is 1D
  and the 3×d code is quasi-1D (snake). **Full 2D d×d surface codes are explicitly future
  work needing PEPS / isoTNS** (Sec. VI, Sec. IV.A). Our end target is the real Google d3/d5/d7
  surface code, which is genuinely 2D — so the **MPS generator is a stepping stone /
  small-width faithful generator + validator, not the final large-d 2D generator.** (Their
  χ = 8/16 remarks for 5×d/7×d are about holding the _noiseless_ logical state; noise
  spreading over long MPOs still inflates cost.)
- **W2 — phenomenological, not device-calibrated, noise.** The authors state the model is
  **not meant to match any specific experiment** (p.2); phases λ_i, φ_i are random, the
  CZ |2⟩ phase is a fixed choice, and **measurement-induced leakage and readout leakage are
  neglected** (Sec. II.C). For a teacher meant to mimic *real* hardware we'd need to
  calibrate these (or fold in the Google datasets), not take the toy constants.
- **W3 — no a-priori error bound; the "exact" reference is internal.** As in §2 above, the
  truncation control is convergence-based, not a certified bound; the only rigorous oracle
  is an *independent* exact simulator, which they don't run — **we supply it** via the exact
  qutrit-DM backend (`src/error_coupling_simulator/carrier/exact/qutrit_dm.py`), which is
  what turns their error-_controlled_ generator into a FAITHFULNESS-_bounded_ one on a d3
  tile.
- **W4 — soft readout is a crude p = 0.5 erasure.** Our "soft readout" axis likely wants a
  continuous/analog IQ-likelihood model; their instrument (Eqs. 8–9) is the **leaked-state-
  randomized** special case, not a full soft-information readout. Useful as a leakage-on-
  readout generation primitive, not as the full soft-readout generator itself.
- **W5 — MWPM-only decoding + LER as the sole reported quantity.** They report only logical
  error rate (and bond dimension); no record-level statistics, no `p_ij` / correlated-tail
  observables, no matched-null discriminability check. Since for us the **record** is the
  deliverable and the decoder/LER is only downstream, we add the {det,obs}-logging plus the
  faithfulness-vs-oracle and anti-toy-vs-null scoring ourselves (the engine supports it;
  they just didn't report it).
- **W6 — not a learning / inference method.** This is a forward simulator only; it does not
  recover channels or fit parameters. That is exactly right for us: the project scope is the
  faithful **forward GENERATOR**, and any recover / characterize / `do()` use is a separate,
  out-of-scope later project (memory `feedback-simulator-is-goal-twin-is-next`). This paper
  contributes the generator, full stop.

## How to use / trust

- **Cite for:** (a) qutrit-MPS-trajectory as a scalable, twirl-free leakage simulator; (b)
  the explicit **>3× GTA-over-prediction** evidence that Pauli/leakage-rate models miss
  decoding-relevant coherent leakage (Fig. 8); (c) the area-law / bounded-χ scalability
  argument (Figs. 5–7); (d) the leakage channel set (Eqs. 1–12) and thermal Kraus map (Eq.
  10) as a ready model; (e) the three leakage-removal strategies (No-reset / MLR / DQLR).
- **Do not cite as:** a 2D d×d surface-code leakage benchmark (it is 1D/quasi-1D); a
  device-calibrated noise model; a method with a certified error bound; or any kind of
  noise-learning / parameter-recovery result.
- **Open questions for our build.** (i) What is the empirical **discarded-weight →
  record-error** map on our exact qutrit-DM cross-check, and does ε = 10⁻⁴ hold for our
  richer (calibrated) leakage while keeping the generated {det,obs} distribution faithful?
  (ii) How far does the area-law-bounded-χ regime extend on the **real** Google noise levels
  (their model is phenomenological)? (iii) Does the leakage record stay **discriminable from
  a matched Markov-k / best-Pauli-DEM null** across the parameter range (the record-level
  analogue of Fig. 8, and the anti-toy-legitimacy gate)? (iv) GPU/batched-SVD trajectory
  throughput at d = 5/7 thin codes — is it enough to emit faithful records at the scale
  downstream studies need?
