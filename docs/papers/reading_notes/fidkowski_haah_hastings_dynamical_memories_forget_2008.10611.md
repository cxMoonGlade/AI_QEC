# Full-text review — L. Fidkowski, J. Haah, M. B. Hastings, "How Dynamical Quantum Memories Forget" (arXiv:2008.10611, Quantum 2021)

> **Provenance (2026-07-11): FULL-TEXT read (精读).** Source txt:
> `docs/papers/fidkowski_haah_hastings_dynamical_memories_forget_2008.10611.txt`
> (2253 lines, arXiv source of arXiv:2008.10611v3 [quant-ph], 30 Jul 2022, 25 pages incl. 3
> appendices). All section/equation references below are to this text. **ID/title verified**:
> header line 1 gives the exact title; author affiliations (U. Washington; Microsoft
> Quantum/Research, Redmond; Station Q, Microsoft Research Santa Barbara) match arXiv metadata.
> "Accepted in Quantum 2021-01-12" banner appears on every page — published in the *Quantum*
> journal (quantum-journal.org), CC-BY 4.0. No figures were pixel-extracted; the two referenced
> figures (Fig. 1, Fig. 2 — numerically simulated purity-vs-steps curves for N=2000) are described
> from their captions and the surrounding body-text discussion only.

## Metadata [paper]

- **Authors / affiliation:** Lukasz Fidkowski (U. Washington), Jeongwan Haah (Microsoft
  Quantum + Microsoft Research), Matthew B. Hastings (Station Q, Microsoft Research Santa
  Barbara + Microsoft Quantum).
- **Venue / status:** arXiv:2008.10611v3 [quant-ph], accepted in *Quantum* 2021-01-12 (peer
  reviewed, published). Rigorous-analysis paper (Schwinger-Dyson / Weingarten-calculus exact
  moment computations + closed-form bounds), with two numerical figures for illustration only.
- **Type:** Theory / rigorous bounds on entanglement-purification dynamics in
  measurement-induced hybrid circuits. NOT a spatial-lattice / local-circuit simulation paper —
  the authors explicitly **discard spatial structure** ("we ignore the spatial structure... The
  system consists of just a single Hilbert space of high dimension N", ln 26–27).
- **Key relationship to our work:** this is a structural/asymptotic companion to the
  measurement-induced phase transition (MIPT) literature it cites as motivation (refs
  [1]-[7]: Li-Chen-Fisher 2018/2019, Skinner-Ruhman-Nahum 2019, Chan et al. 2019, Gullans-Huse
  2020, Choi-Bao-Qi-Altman 2019, Fan et al. 2020) — those papers establish the **p vs. p_c phase
  diagram on a local lattice**; THIS paper does not compute a phase diagram or a p_c. Instead it
  answers a different but crux-adjacent question: does the "mixed"/volume-law phase, if reached,
  persist forever, and how does the answer depend on the **class of unitary** driving the
  circuit (generic/Haar-random "many-body" vs. free-fermion/Gaussian)? It also contains
  (Sec. 4, Discussion) a small worked Pauli/Clifford toy model that is the single most
  crux-relevant passage in the paper.

## Executive summary [paper]

The paper studies a toy dynamical model with **no spatial locality**: a single N-dimensional
Hilbert space subjected to alternating (i) a random unitary and (ii) measurement of one bit of
information (a rank-N/2 projector), tracking a maximally-entangled reference to monitor how a
would-be quantum memory "forgets." Two unitary ensembles are studied: **"many-body"** (Haar
random on the full N-dim space) and **"free fermion"** (Gaussian unitaries + fermion-bilinear
measurements on n modes, N=2^n). Main results, both derived via exact moment calculations
(Schwinger-Dyson equations, Appendix B; Weingarten calculus, Sec. 3.2): (1) in the many-body
case, a maximally mixed state **purifies on a timescale ~N** (exponential in system size), but
with large noisy fluctuations at intermediate times connected to Dyson Brownian motion (Sec. 2);
(2) in the free-fermion case, purification is **much faster, ~n² (polynomial, not exponential)**
— a rigorous proof that **free-fermion monitored dynamics cannot sustain a volume-law/mixed
phase**. Appendix A proves a general, model-independent theorem: von Neumann entropy and
sqrt-purity, **averaged over measurement outcomes, can never increase** on measurement — giving
a hard ceiling on any ensemble-average growth, even though individual trajectories can show
transient decreases in purity (i.e., transient entanglement growth). Section 4's discussion
adds a sharp, easily-checked example: **repeatedly measuring the same fixed set of commuting
Paulis with no intervening unitary purifies in LINEAR time**, whereas Haar/Clifford scrambling
between repeated measurements of a fixed Pauli purifies in time **exponential in n**.

## Method (deep) [paper]

- **Setup (Introduction, ln 26–35):** No lattice, no locality. State ρ on a single N-dim Hilbert
  space, N even. One step = unitary U then measurement of a fixed rank-N/2 projector P0 (i.e. the
  random projector P = UP0U† is equivalent up to gauge to varying the measurement basis each
  step). Purity ≡ tr(ρ²) is the entropy proxy (max 1 pure, min 1/N maximally mixed).
- **Many-body case (Sec. 1):** U Haar-random on U(N). Post-selected update ρ' = tr(Pρ)⁻¹PρP;
  measurement update stochastically branches to Pρ P/tr(Pρ) or (1−P)ρ(1−P)/tr((1−P)ρ) with the
  Born-rule probabilities. Exact 1/N-expansion via Schwinger-Dyson equations (Appendix B, using
  the invariance of the Haar measure under U → e^{iε(M+M†)}U) gives Eq. (4)/(9): average purity
  increase per step = **1/N** to leading order (both post-selected and measurement cases), and
  Eq. (6)/(12): variance per step is also **O(1/N)**. This "drift ~ noise ~ 1/N" balance (Peclet
  number ~1 at t~N) is why the dynamics is diffusive with large fluctuations up to t~N (Sec. 2,
  Dyson Brownian motion analogue, Eq. 14–16).
- **Free-fermion case (Sec. 3):** n fermionic modes, Gaussian states parameterized by an
  antisymmetric 2n×2n correlation matrix M (Majorana basis). A proxy second-Rényi entropy
  S_proxy = (log 2)(n − ½Tr M²) (Eq. 26) is exact on the maximally mixed and all pure Gaussian
  states and bounded close to the true S₂ elsewhere. **Particle-number-conserving** case (Sec.
  3.1): measuring occupation of mode 1 gives ΔS_proxy = −(log2)(1−(M²)₁₁)²/(1−M₁₁²) ≤ 0 (Eq. 29);
  averaged over a Haar-random ensemble this gives Δs ≥ s²/n (Eq. 31, s ≡ entropy density) →
  s(t) ≤ (1+t/n)⁻¹ → half the entropy density lost in time ~n, purity O(1) reached at t~n².
  **General (pairing-allowed) case** (Sec. 3.2): same n² scaling via Weingarten-calculus average
  over SO(2n) (Eq. 33).
- **Control parameter here is NOT a measurement rate p.** The paper's control parameters are (a)
  which **unitary ensemble** drives scrambling between the (always-present) single-bit
  measurements — Haar-random-on-full-space vs. Gaussian/free-fermion vs. (Sec. 4) Clifford — and
  (b) how many linearly-independent stabilizers/measurement outcomes have already been fixed.
  There is no spatial lattice, hence no "local measurement rate per site per round" parameter of
  the kind that sets p_c in Skinner-Ruhman-Nahum / Li-Chen-Fisher / Gullans-Huse.
- **General theorem (Appendix A):** Lemma 2 — von Neumann entropy averaged over measurement
  outcomes cannot increase (proof via a tripartite purification + subadditivity argument).
  Lemma 3 — sqrt-purity averaged over outcomes cannot decrease (Cauchy-Schwarz argument on
  block-diagonal ρ). These are **exact, model-independent** (any POVM), and they are the reason
  the many-body/free-fermion dynamics *must* eventually purify — they give the sign of drift, not
  its rate.

## Results + numbers [paper]

| Quantity | Value / scaling | Where |
|---|---|---|
| Many-body purification time | ~N = 2^n (exponential in # qubits n) | Sec. 1, discussion after Eq. (10); Sec. 4 |
| Many-body purity gain per step | +1/N (drift), noise ~1/N (variance) | Eq. (4), (6), (9), (12) |
| Free-fermion purification time | ~n² (**polynomial**, not exponential in N=2^n) | Sec. 3, Eq. (31), (33) |
| Free-fermion half-entropy-density time | ~n | Eq. (31): s(t) ≤ (1+t/n)⁻¹ |
| "Optimal"/parallel measurement purification | 1 step (n commuting local measurements in parallel, e.g. Z on every qubit) | ln 61–63 |
| Toy Pauli model: fixed-stabilizer repeated measurement (no scrambling unitary) | **LINEAR** time in n | Sec. 4, ln 1161–1183 |
| Toy Pauli model: random-Clifford scrambling + fixed single-Pauli measurement each round | **EXPONENTIAL** time in n; P(new stabilizer commutes with k existing) ~ 2⁻ᵏ | Sec. 4, footnote 7 |
| Rank-2 (single-outcome-pair) closed form | tr ρ²(t) = 1 − 1/(3e^{t/N}−1) (measurement case) | Appendix B.3 |
| Model class studied | Haar-random unitary on full N-dim space; Gaussian/free-fermion unitary + fermion-bilinear measurement; a Clifford/Pauli toy example — **no spatial lattice in any case** | throughout |

No p_c, no exponent for an entanglement-entropy scaling collapse, and no finite-size scaling
data are reported — this is not that kind of paper. The "numbers" that matter are the two
timescale exponents (N vs. n²) and the linear-vs-exponential dichotomy of Sec. 4.

## The regime boundary [paper → the crux]

**This paper does not compute a measurement-rate phase diagram** — say so plainly: the p ≈ 1
mapping to our syndrome circuit is an **analogy**, not something this paper studies directly (no
lattice, no tunable local measurement probability). What it does establish, precisely:

1. **A hard ceiling, not a threshold.** Lemma 2/3 (Appendix A) are exact and model-independent:
   ensemble-averaged entropy cannot increase, and ensemble-averaged sqrt-purity cannot decrease,
   under *any* measurement. So no protocol of repeated measurements can sustain a genuine,
   infinite-time steady-state volume-law/mixed phase — every such "mixed phase" is at best
   **metastable up to some finite (possibly huge) purification time**, after which the system
   necessarily collapses toward purity 1 (bounded/area-law-like, in the sense of "eventually
   disentangles"). The *only* question is the **timescale**, which is where the paper's real
   content lives.

2. **The timescale is dictated by the unitary class, not by a rate p.** Two regimes are proven:
   - **Generic/Haar-random ("many-body") scrambling** → purification time ~N = 2ⁿ, i.e.
     *exponential* in system size. For all practical purposes this looks like a genuine
     volume-law/mixed phase at any accessible circuit depth — this is the regime a real
     measurement-induced-phase-transition "mixed phase" (p<p_c) lives in.
   - **Free-fermion/Gaussian scrambling** → purification time ~n² (polynomial). The paper states
     this explicitly as: *"a volume law phase for the entanglement entropy cannot be sustained in
     a free fermion system"* (abstract) — i.e. for this **model class**, there is no genuine
     mixed/volume-law phase at all, only an area-law-like ("purifying") regime, consistent with
     the free-fermion MIPT literature they cite (refs [13]–[16]: Cao-Tilloy-DeLuca, Chen-Li-
     Fisher-Lucas, Ippoliti et al., Nahum-Skinner) which finds free-fermion/Gaussian monitored
     circuits have at most a *critical* (log-law) phase, never a stable volume law.

3. **Section 4's minimal Pauli/Clifford toy model is the single most load-bearing passage for
   our crux, and it is a STRUCTURAL (not measurement-rate) argument:**
   - Repeatedly measuring the **same fixed set of commuting Paulis Z1, Z2, Z3, ...** with **no
     intervening unitary** purifies **linearly** in n: each measurement either adds a new
     independent stabilizer (cutting entropy by exactly 1 bit) or is redundant, and this must
     happen at least once every constant number of steps because the operators are fixed and
     commuting (ln 1161–1183). This is the paper's proxy for a **syndrome-extraction-like
     protocol**: the "geometry"/"structure" that matters is not a rate but *whether the same
     stabilizer generators are measured over and over without deep scrambling in between.*
   - By contrast, measuring a **fixed single Pauli** but applying a **new random Clifford**
     before each measurement makes the *effective* operator measured a uniformly random Pauli
     each round; the probability it commutes with the k stabilizers already fixed is 2⁻ᵏ
     (footnote 7) → purification time **exponential** in n. This is the genuine "mixed phase"
     analogue — deep scrambling *between* measurements is what buys exponential (i.e. effectively
     unbounded on any practical timescale) persistence of a volume-law/mixed regime.
   - **The controlling variable this section isolates is therefore: how much unitary
     scrambling happens between successive measurements of (near-)the same stabilizer group,
     not how many sites are measured per round.** A circuit that measures "all" ancillas every
     round (p≈1 in the naive rate language) but does so via *shallow, local, structured* gates
     that repeat the *same* stabilizer set is structurally the LINEAR/fast-purifying case, even
     though its raw measurement density is maximal.

4. **Caveat that could push toward growth, taken directly from the paper's own numerics
   (Fig. 1/2, Sec. 2):** the ensemble-average bound (Lemma 2/3) says nothing about **individual
   trajectories** — a single trajectory's purity can *decrease* (entanglement can *grow*) for
   extended stretches at intermediate times ("one can observe long fluctuations in which the
   purity decreases for many steps", ln 78–79) before ultimately collapsing to purity ≈1; this
   is exactly the noisy middle regime of Fig. 1/2, connected to Dyson Brownian motion (Sec. 2).
   A single-wire/single-trajectory carrier (which is what our PEPS build is) tracks *one*
   measurement record, not an ensemble average — so a 2-round bond spike (4→18→>40) sits
   entirely inside the kind of transient, non-monotone behavior this paper's own figures show is
   normal for individual trajectories, even in a system that *will* eventually purify/saturate.
   This paper gives no tool to distinguish "transient trajectory noise that will resolve by
   round ~n or ~n²" from "genuine sustained volume-law growth" from only 2 rounds of data.

5. **No genuine geometry/lattice dependence is studied** (the model has none by construction);
   the only "structural" axis found is the unitary-class / repeated-vs-fresh-stabilizer axis of
   points 2–3 above. Any statement mapping this to a 2D rotated-XZZX syndrome circuit's actual
   geometry (weight-4 stabilizers, boundary conditions, ancilla connectivity) is an extrapolation
   from a non-spatial toy model, not a result of this paper.

## Relevance to the d5 PEPS crux [ours]

**Net verdict: this paper leans toward supporting "bond should saturate (area-law/bounded)" for
a genuine syndrome-extraction circuit, via a STRUCTURAL argument (repeated fixed-stabilizer
measurement, no deep scrambling) rather than via a measurement-rate argument — but it also
supplies the honest caveat for why a 2-round pilot spike is inconclusive either way.**

- Our d5 rotated-XZZX syndrome-extraction circuit, each round, measures (very close to) the
  **same fixed set of stabilizer generators** using shallow, local, structured CNOT/CZ networks —
  it does not interleave deep, generic (Haar/near-Haar) scrambling unitaries between measurement
  rounds. This maps far more closely onto the paper's Sec. 4 **"repeated fixed-Z measurement, no
  scrambling unitary → linear-time purification"** case than onto its **"random-Clifford-scrambling
  + fixed-Pauli → exponential purification"** case. If that mapping holds even qualitatively, it
  argues the physical entanglement generated per round should be *disentangled* about as fast as
  it is generated — i.e. **bounded, area-law-in-circuit-time**, consistent with our hypothesis
  that the compiled weight-4 √E_s POVM instrument (not the physics) is responsible for the
  observed 4→18→>40 bond blow-up.
- This is reinforced, independently, by the paper's model-independent theorem (Appendix A,
  Lemma 2/3): the *ensemble-averaged* entropy of our syndrome record can never increase round over
  round — there is a hard theorem-grade ceiling on sustained growth *in expectation*, regardless
  of geometry. That ceiling doesn't by itself bound the *bond dimension* of a single-trajectory
  PEPS carrier, but it is independent, exact corroborating evidence that "genuinely growing,
  never-saturating entanglement" is not the generic expectation for a repeated-measurement
  protocol like ours.
- **The countervailing caveat (do not over-read the growth-supports-bound conclusion):** this
  paper's own Fig. 1/2 dynamics show individual trajectories can show sustained, non-monotone
  purity *decrease* (entanglement growth) over many steps before eventual saturation — and the
  free-fermion "fast ~n² purification" and many-body "slow ~N purification" results show the
  *timescale* to reach the bounded regime can vary enormously depending on microscopic structure.
  A 2-round pilot is far too short a window, by this paper's own timescale language, to
  distinguish "artifact-driven unbounded growth" from "genuine but slow-saturating growth toward
  a large-but-finite plateau." The paper gives no basis for asserting our specific bond
  dimension will saturate at any particular value or timescale for a 2D geometric circuit — only
  that *some* saturation timescale should exist unless our per-round dynamics is structurally
  closer to the paper's "deep scrambling between fixed measurements" exponential case (which our
  circuit's shallow, local, repeated-stabilizer structure argues against).
- **Model-class mismatch to flag honestly:** neither of this paper's two proven regimes (Haar
  many-body on a featureless N-dim space; Gaussian/free-fermion) is our model. Our carrier is a
  qutrit MCWF/PEPS trajectory over a genuine 2D lattice with local weight-4 stabilizer POVMs and
  leakage — structurally much closer to the "Clifford/Pauli toy" of Sec. 4 (a stabilizer circuit)
  than to either of the paper's two rigorously analyzed classes. The linear-vs-exponential
  dichotomy of Sec. 4 is stated as an easy illustrative aside, not proved with the same rigor as
  the many-body/free-fermion results — treat it as a strong qualitative pointer, not a theorem
  we can cite as settling the question.

## How to use / trust + open questions [ours]

- **Trust level:** FULL-TEXT 精读 (2253 lines / 25 pages incl. appendices). The many-body and
  free-fermion results (Sec. 1, 3, Appendices A–C) are rigorous, exact-moment derivations
  (Schwinger-Dyson / Weingarten calculus) — high confidence, PROVEN, for the stated (non-spatial)
  model classes. The Sec. 4 Pauli/Clifford toy-model dichotomy is presented informally ("it is
  easy to see...") with a one-paragraph combinatorial argument (footnote 7) — plausible and
  checkable by direct calculation, but not proved with the same rigor; independently verifiable
  in an afternoon by simulating small stabilizer-tableau circuits.
- **Independent-orability:** the Sec. 4 linear-vs-exponential claim is directly checkable by a
  small stabilizer-simulator experiment (e.g. Stim or a hand-rolled tableau) — measure a fixed
  commuting Pauli set repeatedly (expect linear purification) vs. interleave random Cliffords
  before measuring a fixed Pauli (expect exponential) — this would be a cheap, independent
  sanity check before leaning further on the paper's qualitative mapping to our circuit.
- **Open questions for the PEPS-crux investigation:**
  1. Does a *genuinely local, 2D, weight-4-stabilizer* syndrome circuit (not the paper's
     featureless-Hilbert-space or all-to-all free-fermion models) actually sit in the
     "linear/fast purification" bucket of Sec. 4, or does the local geometry (finite-depth
     light cone per round) reintroduce something closer to the exponential/scrambling case at
     larger code distance? This paper cannot answer that — only the genuine MIPT-on-a-lattice
     literature (refs [1]-[7], esp. Choi-Bao-Qi-Altman on scrambling+QEC) can.
  2. Is our pilot's bond growth (4→18→>40 over 2 rounds) inside the "noisy intermediate regime"
     this paper's Fig. 1/2 shows is generic for single trajectories, or is it already anomalously
     large relative to what any structural argument here would predict? Running more rounds
     (the paper's own timescale argument implies looking well past round ~2-3 is necessary before
     concluding anything about saturation) is the direct empirical test.
  3. Do the compiled weight-4 √E_s POVM's ancilla-coupling gates constitute "shallow local
     structured" scrambling (paper's linear-time bucket) or do they, via leakage/non-Pauli
     structure, effectively re-randomize the measured operator each round in a way closer to the
     paper's "random Clifford before fixed-Pauli" exponential bucket? This is exactly the
     mechanism-level question the instrument-artifact hypothesis needs to rule in/out — this
     paper supplies the conceptual axis (repeated-fixed-operator vs. re-randomized-operator) but
     not the answer for our specific compiled instrument.
