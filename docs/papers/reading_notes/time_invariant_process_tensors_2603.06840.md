# Full-text review — Cochin, Keeling, Lovett, Chin, "Efficient construction of time-invariant process tensors for simulating high-dimensional non-Markovian open quantum systems" (arXiv:2603.06840)

> **Provenance (2026-06-30): FULL-TEXT read (精读).** PDF `outputs/papers/2603.06840.pdf` → txt
> `outputs/papers/2603.06840.txt` (PyMuPDF, 13 pp, 60993 chars). All §/Eq/Fig/App refs from that text.
> Figures not pixel-extracted — figure facts = captions + numbers stated in the text.
> **2026 preprint (v1, dated 2026-03-10, submitted 6 Mar 2026) — treat all quantitative scaling claims
> as PROVISIONAL, not peer-reviewed.**

## Metadata [paper]
- Authors: Émile Cochin (ENS de Lyon / St Andrews / Sorbonne–INSP); Jonathan Keeling, Brendon W. Lovett
  (St Andrews SUPA); Alex W. Chin (Sorbonne–INSP / CNRS). Same group behind OQuPy / TEMPO / process-tensor
  lineage.
- Venue / status: arXiv:2603.06840v1 [quant-ph], 6 Mar 2026. Preprint, no journal. All sims via open-source
  **OQuPy** [55,56].
- Type: numerical-methods (algorithm + tensor-network) with a circuit-QED application demonstration.

## Executive summary [paper]
Process tensors (PT) are MPO representations of a Gaussian environment's influence functional; a
**time-translationally-invariant PT (TTI-PT)** [Link et al. 25] makes long-time (many-timestep) evolution
cost O(τ), independent of the number of timesteps n. The unsolved bottleneck was the **scaling with SYSTEM
Hilbert dimension d**: building the TTI-PT via iTEBD cost ~O(d⁸) in time and stored χ²d⁴-element tensors.
This paper inserts **intermediate SVD compression steps** into the iTEBD gate contraction — first compressing
the `b(k)` influence gate (rank d² → α), then partial SVDs on the left/right blocks (→ β₁, β₂ ≪ d²), so the
central iTEBD SVD runs on a reduced χβ₁ × χβ₂ matrix instead of the full χd² × χd². Empirically this brings
time **O(d⁸) → O(d⁴)** and memory from χ²d⁴ → ~χ²d² (Fig. 4), with orders-of-magnitude gains beyond ~a dozen
levels. Demonstrated on dispersive qubit readout in circuit QED (a driven resonator, d up to 30–40 levels,
tens of thousands of timesteps, structured/Purcell-filtered spectral density) — previously out of reach.

## Method (deep) [paper]

**System–environment model** (Eq. 1, §II A). Single composite system `Ĥ_S` linearly coupled through ONE
system operator `Ŝ` to a **Gaussian (bosonic) bath**:
```
Ĥ_SE = Ĥ_S⊗1 + Ŝ⊗Σ_k (h*_k b̂_k + h_k b̂†_k) + 1⊗Σ_k ω_k b̂†_k b̂_k          (1)
```
Bath fully characterized by spectral density `J(ω) = Σ_k |h_k|² δ(ω − ω_k)`. Work in the eigenbasis of `Ŝ`
(diagonal), Liouville indices `μ = (μ_l, μ_r)`.

**Reduced dynamics via process tensor** (Eq. 2). After Trotterization (exact as Δt→0):
```
ρ_{μ_n}(t_n) = Σ_{μ_0..μ_n} F_{μ_0..μ_n} Π_{i=1}^n (U_{S,μ_iμ_{i-1}}) ρ_{μ_0}(0)      (2)
```
`U_S = e^{-i[Ĥ_S,·]Δt}`; `F` = discretized Feynman–Vernon influence functional.

**Influence tensor** (Eqs. 3–6), triangular tensor network:
```
F_{μ_0..μ_{n-1}} = Π_{i=0}^{n-1} Π_{j=1}^i [ b^{μ_j}_{μ_i}(i−j) ]                       (3)
b^{μ_j}_{μ_i}(i−j) = exp[ −(λ^{μ_l}_i − λ^{μ_r}_i)(η_{i-j} λ^{μ_l}_j − η*_{i-j} λ^{μ_r}_j) ]  (4)
```
`λ_μ` = eigenvalues of `Ŝ`. `η_{i-j}` = double time-integral of the bath correlation function `C(t)` (Eqs. 5–6):
`C(t) = ∫_0^∞ dω J(ω)[coth(ωβ/2) cos ωt − i sin ωt]`, β = inverse temperature.

**Recast to 2D network** (Eq. 7): expand `b` with extra legs, `b̃^{μν}_{ab}(k) = δ_{ab}δ_{μν} b^μ_b(k)` for
k>0 (Fig. 1c) → triangular 2D tensor network contractible into an MPS/MPO.

**TTI-PT via iTEBD** (§II A, from Link et al. [25]): expand the triangular network to infinite time (Fig. 1a),
reshape into a translationally-invariant 2D network (Fig. 1b), contract with **iTEBD** [32] — a two-site
(A, B) canonical-gauge infinite MPS. At each step the `b̃(k)` gate is contracted, MPS truncated to bond dim χ,
re-canonicalized, sites swapped for gate `b̃(k−1)`. Network truncated at memory depth `k̃` (where `C(k̃Δt)`
has decayed). Largest correlations `η_k` are contracted LAST → χ grows most at the end.

**The bottleneck** (§II B): the regular iTEBD step builds a χd² × χd² matrix and SVDs it → time **O(χ³d⁶)**
(worse in practice since χ grows with d); the intermediate matrix has χ²d⁴ elements. This is worse than the
final PT which needs only χ²d² elements.

**The enhancement — three intermediate SVDs** (§II B, Fig. 2):
1. **SVD the `b(k)` gate** (Eq. 8): `b^μ_b(k) = Σ_{i=1}^α U_{bi} Λ^k_i V_{iμ}`. When η_k and the eigenvalue
   range of `Ŝ` are small, `b(k)` is an exponential of a small low-rank polynomial → highly compressible;
   truncate d² → **α**, "often a fraction of d²."
2. **Partial SVDs on left/right blocks** (Eq. 9, Fig. 2c): `θ^A_{b[ilm]} = Σ_{q=1}^{β₁} U^A_{bq} V^A_{qilm}`,
   `θ^B_{μ[ipm]} = Σ_{r=1}^{β₂} U^B_{μr} V^B_{ripm}`; grouping the d²-size legs, truncate to **β₁, β₂ ≪ d²**.
3. **Central iTEBD SVD on the reduced Θ block** (Eq. 10, Fig. 2d), excluding the U^A, U^B unitaries:
   `Θ_{qrlp} = Σ_{i=1}^α Σ_{m=1}^χ V^A_{qilm} V^B_{ripm} Λ^A_{mm} Λ^k_{ii}`. SVD runs on the **χβ₁ × χβ₂**
   `Θ_{[qp][rl]}` matrix, NOT the full χd² × χd². The leftover U^A, U^B are contracted back only in the
   next iteration's step (c). **This avoids ever building a χ²d⁴-element tensor.**

Key idea (partial SVD to shrink the big iTEBD SVD) also appeared generically in Xu [35]; here the additional
first `b`-reduction (α ≪ d²) makes β₁, β₂ also ≪ d². Authors tested SVDing the χ-legs instead (as Xu) and
found their d²-leg choice optimal here.

**Accuracy control** = `ϵ_rel` on the final Θ SVD (keep singular values > ϵ_rel × largest); the other three
SVDs truncated at fixed relative 1e-7. Memory depth `k̃` sets how far back correlations are kept.

## The MECHANISM (for implementation) [paper → ours]
This is an **environment/oracle engine**, not a channel definition. What it produces = an exact
(non-Markovian, Gaussian-bath) simulator of a driven-dissipative single composite system. Concrete
demonstrated instance (§III, the piece relevant to us):
- **Model**: qubit + driven resonator + structured readout line as a Gaussian bath (Rabi Hamiltonian
  Eq. 13, non-RWA sine drive Eq. 15, coupling `(â+â†)` to the bath Eq. 16).
- **Structured spectral density** (Eq. 17): `J_p(ω) = 2ηω exp(−ω/ω_c) H_p(ω−ω_q)`, with a **notch (Purcell)
  filter** `H_p(ω) = 1 − p exp(−ω²/w²)`, 1/w² = 150, filter strength p ∈ {0, 0.25, 0.5, 0.75, 0.9}. This is
  the "beyond smooth-lineshape" structured-bath capability — the ability to put a SHARP spectral feature at
  a chosen frequency where Lindblad expansions are known to fail (§III B, [51]).
- **Grounded params** (Fig. 6): g = 0.211 GHz, ω_q = 5.304 GHz, ω_r = 7.5 GHz, η = 1e-3, ω_c = 3ω_r,
  κ ≈ 0.068 ns⁻¹; TTI-PT with k̃ = 1000, ϵ_rel = 1e-7, Δt = 2πω_r/62, N = 20 resonator levels.
- If we wanted this: it is **OQuPy** (their open-source package) — we would not re-implement the iTEBD.

## The OBSERVABLE / metric [paper]
- **Purcell decay rate** γ = 1/T₁, extracted by fitting ⟨σ̂_z(t)⟩ to a decaying exponential over the last
  third of the run (Fig. 6). Fermi-golden-rule baseline `γ_JC = (g²/Δ²) J_p(ω_q)` (Eq. 18); the Rabi
  correction `γ = [2ω_r/(ω_r+ω_q)]² γ_JC = 4g²ω_r²/(ω_q²−ω_r²)² J_p(ω_q)` (Eq. 19). Note J evaluated at
  **ω_q**, not ω_r — and the drive shifts it to `J_p(ω̃_q)` via ac-Stark `ω̃_q = ω_q + χ(2n̄+1)`,
  χ = g²/Δ² (§III B 1, App. B Eq. B1).
- **Readout-fidelity histograms**: p-quadrature distributions ⟨p|ρ|p⟩ for up/down qubit (Fig. 7);
  infidelity = histogram overlap.
- **INSUFFICIENCY flagged**: the naive single-dissipator Lindblad (App. C, Eq. C1–C2, κ = 2πJ(ω_r)) is
  **insensitive** to (i) Rabi-vs-JC Hamiltonian and (ii) any spectral-density variation between ω_r and ω_q.
  It only reproduces the exact rate when J is flat + weak + RWA valid (App. C, Fig. 10, <0.2% infidelity).
  As soon as a sharp notch or the Rabi correction matters, Lindblad fails — that is the paper's raison d'être.

## Findings + numbers [paper]
- **Scaling**: time **O(d⁸) → O(d⁴)** (Fig. 4b, §II C, Conclusion); memory χ²d⁴ → ~χ²d² (matrix-free θ SVDs
  give the χ² max(d², β₁β₂) bound, and β₁β₂ < d² at large d). Enhanced method is faster at ALL d despite
  three extra SVDs. Intermediate bonds α, β₁, β₂ all ≪ d² (Fig. 3); final χ agrees between old/new (no info
  lost). β₁ ≠ β₂ because b(k) is not symmetric.
- **Demonstrated regime**: harmonic-oscillator benchmark up to d = 40; circuit-QED application at N = 20–30+
  resonator levels, tens of thousands of timesteps, k̃ = 500–1000.
- **Physics result**: with the ohmic (unfiltered) bath, γ DECREASES with drive; with strong Purcell filters
  the trend REVERSES (γ increases with drive), matching experiment — attributed to ac-Stark shift moving ω̃_q
  into a higher-J region of the notch (App. B, Fig. 9, qualitative not exact).
- **Validation** (App. A): vs an exactly-solvable Bogoliubov/chain-mapped quadratic model (no qubit),
  d = 30, 4200 bath modes (8400×8400 diagonalization) — **relative error ~0.3%**, growing with time,
  <1% at Purcell-extraction times. (App. C: vs Lindblad on flat bath, <0.2% infidelity, rate within 1%.)
- Hardware: Intel Xeon Gold 5218 @ 3.9 GHz, 32 cores (CPU benchmarks).

## Limitations [paper]
- **SINGLE composite system + a Gaussian bath.** Coupling is ONE system operator `Ŝ` to a bosonic
  (Gaussian) environment. The whole efficiency story is about d = the dimension of that ONE system.
- **Multi-site / chain / spatially-coupled sites = EXPLICITLY OUT OF SCOPE / FUTURE WORK.** Direct quotes:
  - "simulations with the full transmon space require enhancements ... **This could be done for example by
    treating the coupled qubit-resonator system as a chain of two quantum systems** ... as efficient methods
    have recently been developed for propagating process tensors with chain systems **[30]**." (§III)
  - "going beyond the currently existing methods which are restricted to coupling operators with degenerate
    eigenvalues [29] or **chain-like systems [30]**." (Conclusion) — i.e. chain-systems are a SEPARATE method
    (ref [30]), not this one.
  - The demonstrated 2-body case (qubit+resonator) is handled by a **degeneracy trick**, NOT by this
    algorithm: because `(â+â†)` acts only on the resonator, the TTI-PT is built for the N-level resonator
    alone and "applied only to the resonator leg" — "analogous to the original use of degeneracies to
    simplify path summation [29]." (§III B) The qubit rides along; it is not a second coupled bath site.
- **Gaussian bath only** (though reaction-coordinate mapping [54] can bring some non-Gaussian couplings into
  the system — Conclusion). No fermionic/spin baths.
- **Long-lived bath correlations remain hard** (large k̃ → cost); process tensors are known to struggle with
  a dominant sharp bath mode ([53], Conclusion).
- **Error control is a-posteriori (convergence), not a-priori**: accuracy is governed by SVD truncation
  ϵ_rel + memory depth k̃ + Δt + level truncation N; validity shown empirically by benchmarking vs an exact
  reference (App. A), not by a proven a-priori bound. The "O(d⁴)" itself is an **empirical fit** — the
  authors state the true scaling "is harder to estimate ... due to all the various contractions and SVDs"
  and "we observe from the benchmarks an improvement from an approximate O(d⁸) to O(d⁴)."
- Building/diagonalizing the combined system–TTI-PT propagator "can become untractable for large system
  sizes" — an open bottleneck they flag (Conclusion).

## Relevance to qec_twin (the twin) [ours]
Our live need (from CLAUDE.md + MEMORY): a **non-Markovian SHARED-BATH teacher** for coupled QEC qubits
(TLS / 1/f / shared-bath source), where the wedge is **CP-divisibility breaking / coherence revival**, plus
an **independent oracle** to certify the carrier. Map against that:

- **Multi-site coupled qubits — NO.** This is the decisive point. The method is a single-system-vs-Gaussian-
  bath engine; the ONLY 2-body demo works by a degeneracy shortcut (Ŝ acts on one subsystem), and genuine
  spatially-coupled / chain systems are explicitly deferred to ref [30] (a DIFFERENT algorithm). A shared
  bath simultaneously coupling ≥2 QEC data qubits — each contributing its own `Ŝ_i` to a common `J(ω)` — is
  NOT what this builds. So it is **NOT a drop-in shared-bath teacher** for our correlated-source axis.
- **As an ORACLE — YES, narrow and valuable.** It IS an *independent*, exact-in-the-limit non-Markovian
  reference for a SINGLE mode/qubit + a Gaussian structured bath, benchmarkable to ~0.3% against a
  from-scratch chain-mapped Bogoliubov solve (App. A). That satisfies FAITHFULNESS-PROTOCOL rule (I):
  ground truth INDEPENDENT of our implementation. If we ever need to certify a single-qubit non-Markovian
  dephasing/relaxation channel (T1/T2 with a structured/notched spectral density) it is a legitimate
  independent oracle — via **OQuPy**, no re-implementation.
- **As a CARRIER — NO.** It does not scale to a 50+ qubit surface-code lattice; d is a single composite
  system's dimension and the whole point is one small system + one bath. Our carrier stays the MPS/MPDO
  leakage engine (ADR 0010). This is orthogonal.
- **Structured-bath physics we can REUSE conceptually**: the notch/Purcell spectral density (Eq. 17) and the
  proven-INSUFFICIENCY of a single-dissipator Lindblad when the bath is sharp (App. C) is a clean, citable
  statement that **Lindblad ≠ exact once the bath has structure at ω_q** — directly supportive of our
  "non-Markovian IS the contribution / Markov-k-captures-classical-corr is a strawman" thesis
  (project-nonmarkovian-wedge-must-be-coherence). But note their observable is a RATE (γ, an incoherent T1),
  extracted from ⟨σ_z⟩ decay — it does NOT by itself demonstrate the coherence-revival / CP-divisibility
  signature we decided the wedge must be. The engine CAN produce ⟨σ_x⟩/⟨σ_+⟩ multi-time correlations (they
  cite multi-time-correlation capability [21,28]), so a Ramsey/echo |L(t)| non-monotonicity IS computable in
  principle — but only for the single-system case.
- **CORRECTION it forces on a prior assumption**: none of our channel definitions; but it tempers any hope
  of using PT/TTI-PT as the correlated-multi-qubit shared-bath teacher — that path needs the chain-system PT
  method [30] (Riva/Le Dé et al.), NOT this one. Flag ref [30] as the next paper to read if we pursue a
  PT-based coupled teacher.

**Verdict class**: **ORACLE (single-qubit / single-mode structured non-Markovian, via OQuPy)** — usable and
independent for T1/T2-with-structured-J certification. **N/A as a coupled-shared-bath teacher and as the
carrier.** Trade-off: exactness + genuine non-Markovianity for ONE small system, at the cost of no
multi-site coupling. **PROVISIONAL** — 2026 v1 preprint, O(d⁴) is an empirical fit not a theorem.

## How to use / trust + open questions [ours]
- **Trust**: FULL text read; figures not pixel-extracted (numbers taken from captions/text). Method equations
  (1–10, 17–19, B1, C1–C3) transcribed verbatim. Preprint → provisional; the headline O(d⁸)→O(d⁴) is an
  empirical benchmark fit (their own hedge), not a proven complexity bound.
- **GT-feasibility for us**: HIGH for the single-mode oracle role — OQuPy is open-source [55,56], and their
  own independent check (chain-mapped Bogoliubov, App. A) is itself reproducible from-scratch, giving a
  double-independent path.
- **Open questions before any use**: (1) Is our correlated-source teacher genuinely a shared bath needing
  multi-site PT (→ read ref [30], the chain-system PT method), or can we decompose it into per-qubit
  single-bath oracles this method covers? (2) Does the OQuPy TTI-PT expose the multi-time correlators we'd
  need for a |L(t)| coherence-revival oracle, and at what k̃/χ cost for our T1/T2 regimes? (3) Reaction-
  coordinate mapping [54] — could it fold a dominant TLS mode into the system so the residual bath is
  Gaussian-and-tractable? (worth checking against our TLF-1/f source seed).

## Provenance
FULL-TEXT 精读 of arXiv:2603.06840v1 (2026-03-10). PDF→txt via
`.claude/skills/theory-first/scripts/fetch_and_extract.py 2603.06840` (PyMuPDF, 13 pp). Read
`.claude/skills/theory-first/references/reading_note_template.md` first. Note author: theory-first workflow,
2026-06-30.
