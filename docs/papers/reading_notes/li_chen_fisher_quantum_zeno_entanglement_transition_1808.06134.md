# Full-text review — Y. Li, X. Chen & M. P. A. Fisher, "Quantum Zeno Effect and the Many-body Entanglement Transition" (arXiv:1808.06134v2, Nov 2018)

> **Provenance (2026-07-11): FULL-TEXT read (精读).** Source txt =
> `docs/papers/li_chen_fisher_quantum_zeno_entanglement_transition_1808.06134.txt`, 2821 lines
> (arXiv-source-derived plain text, includes garbled figure-legend character soup around Figs. 3-6
> that was skipped as non-load-bearing — all numeric/equation content around it is intact and
> cross-checked against the caption text). ID/title verified against the paper's own header
> (`arXiv:1808.06134v2 [quant-ph] 19 Nov 2018`, "Quantum Zeno Effect and the Many-body Entanglement
> Transition", Y. Li, X. Chen, M. P. A. Fisher, UCSB/KITP). This is one of the three simultaneous
> founding papers of the measurement-induced entanglement phase transition (MIPT) literature — the
> "Note added" (line 2674) explicitly cross-references the other two same-day postings: Chan,
> Nandkishore, Pretko, Smith (arXiv:1808.05949) and Skinner, Ruhman, Nahum (arXiv:1808.05953). Only
> this paper (Li-Chen-Fisher) was close-read for this note; the other two are NOT covered here.

## Metadata [paper]

- **Authors / affiliation:** Yaodong Li (UCSB Physics), Xiao Chen (KITP UCSB), Matthew P. A. Fisher
  (UCSB Physics + KITP).
- **Venue / status:** arXiv:1808.06134v2 [quant-ph], posted 19 Nov 2018 (original Aug 2018). One of
  the three founding MIPT papers (published later in Phys. Rev. B / similar; the arXiv text itself
  does not state a final journal in the header).
- **Type:** Analytic model definition + extensive numerics (exact statevector simulation up to
  L=16 for Haar circuits; Clifford stabilizer-formalism simulation up to L=512 for the
  phase-transition study). No experiment; no PEPS/PEPO; **1D chain only**.
- **Key relationship to our work:** THE foundational paper establishing that projective measurement
  rate `p` in a random unitary circuit drives a continuous entanglement phase transition between a
  volume-law "weak measurement" phase and an area-law "quantum Zeno" phase. This is the primary
  physics reference for why our syndrome-extraction PEPS carrier (near-maximal per-round
  measurement) should sit deep in an area-law-like regime — but the paper's own numbers show the
  transition point `p_c` is **not universal** and depends sensitively on the *structure/rank* of the
  measurement operator, which is the central caveat for mapping this result onto a real stabilizer
  circuit.

## Executive summary [paper]

The paper defines a 1D brickwork "hybrid" quantum circuit: at every gate location, with probability
`p` a projective measurement is performed just before a 2-qubit unitary (a "UP" gate), and with
probability `1-p` only the unitary acts (a "U" gate). Two choices of local unitary ensemble (Haar
random on U(4), and uniform random 2-qubit Clifford) and two choices of measurement projector
(rank-1 "both-qubit" Z-basis projectors, and rank-2 "parity" Z₁Z₂ projectors) are studied. At `p=1`
(measurement before every unitary) the system provably/numerically saturates to an **area law** —
the "quantum Zeno phase." At `p=0` it is the known volume-law random-unitary-circuit result. As `p`
is tuned continuously between 0 and 1, the paper finds — using the Clifford models to reach L up to
512 — a genuine continuous phase transition at a critical `p_c` that is **different for the two
projector choices**: `p_c=0.15` for rank-1 projectors, `p_c=0.68` for rank-2 (parity) projectors.
Below `p_c` the volume-law coefficient is nonzero (shrinking continuously to zero as `p→p_c⁻`);
above `p_c` the area-law value diverges continuously as `p→p_c⁺`. At criticality the entanglement
entropy scales sub-linearly, `S_A(p_c, L_A) ~ L_A^γ` with `γ≈1/3` — intermediate between area and
volume law, not either extreme. Finite-size + finite-time scaling collapses give critical exponents
`ν≈1.75-1.85`, dynamic exponent `z≈1` (conventional dynamical scaling, not activated).

## Method (deep) [paper]

**Circuit definition (Sec. II, Fig. 1):** L qubits on a 1D chain, open boundary conditions,
brickwork structure: each discrete time step has two layers (odd bonds, then even bonds), each
gate acting on 2 neighboring qubits. Each gate site is independently drawn to be:
- a plain unitary gate `U` (probability `1-p`): `|ψ⟩ → U|ψ⟩` (Eq. 1);
- a "unitary-projective" gate `UP` (probability `p`): `|ψ⟩ → U P_α|ψ⟩ / ‖P_α|ψ⟩‖` (Eq. 2), where
  `{P_α}` is a complete set of orthogonal projectors and outcome `α` occurs with Born probability
  `p_α = ⟨ψ|P_α|ψ⟩`.

**Two measurement-projector choices (Sec. II, Eqs. 10-15):**
1. **Rank-1 ("both-qubit" Z-basis), model set (1)/B1:** `P_ab = |↑↑⟩⟨↑↑|` etc. for
   `a,b∈{0,1}` — four rank-1 projectors = measuring both `Z₁` and `Z₂`. After one such measurement
   the pair is in a computational-basis product state, **fully disentangled** from the rest of the
   chain.
2. **Rank-2 (parity-only Z₁Z₂), model set (2)/B2:** `P₀⁽²⁾=|↑↑⟩⟨↑↑|+|↓↓⟩⟨↓↓|`,
   `P₁⁽²⁾=|↑↓⟩⟨↑↓|+|↓↑⟩⟨↓↑|` — measuring only the parity `Z₁Z₂`, leaving one qubit's worth of
   residual freedom unresolved. The paper explicitly flags (ln 322-331) that these rank-2
   projectors are "expected to be less effective in suppressing the entanglement entropy," and that
   in the pure-measurement `p=1` limit *without* interleaved unitaries this projector set alone still
   leaves volume-law entanglement (random Page-state argument).

**Two unitary ensembles:** (A) Haar-random 2-qubit unitaries (CUE) — models A1/A2, used for the
`p=1` Zeno-phase study, statevector-simulated up to L=16. (B) Uniform-random 2-qubit Clifford
unitaries — models B1/B2, used for the full `p∈[0,1]` phase-transition study via the stabilizer
formalism (Gottesman-Knill), reaching L up to 512 because Clifford circuits with Pauli-group
measurements remain classically efficiently simulable exactly.

**Observable:** second Rényi entropy `s₂(ρ)=-log₂ Tr ρ²` (Eq. 9) of the reduced density matrix of a
subsystem A under the bipartite cut, computed on the pure quantum-trajectory wavefunction
`|ψ(t)⟩` and averaged over an ensemble of trajectories (random unitaries + random measurement
locations/outcomes; ~10² samples per data point). This bipartite Rényi/entanglement entropy is
exactly the log₂ of the effective Schmidt rank across the cut — i.e. the quantity that lower-bounds
the **MPS/PEPS bond dimension** needed to represent the state exactly across that cut.

**Control parameter:** the measurement rate `p` — the probability that any given brickwork gate
slot is a measurement+unitary rather than a bare unitary. `p=0` = pure random-unitary circuit
(known volume law, Nahum et al. refs [12-14]); `p=1` = measurement before every gate.

## Results + numbers [paper]

| Quantity | Value | Where |
|---|---|---|
| Zeno-phase check, `p=1`, rank-1 projectors (model A1) | Area law: `S_A(L_A)` essentially flat vs `L_A`; entanglement bounded **exactly** at O(1) at all times (rigorous local argument, not just numerics) | Sec. III A, Fig. 2(a,c) |
| Zeno-phase check, `p=1`, rank-2/parity projectors (model A2) | Also consistent with area law numerically, but with **stronger residual L-dependence** (sub-extensive but not as flat as A1) — parity projectors are "less effective" | Sec. III A, Fig. 2(b,d) |
| Critical measurement rate, rank-1 projectors | `p_c = 0.15` (model B1) | Sec. III B, Fig. 3(a) |
| Critical measurement rate, rank-2/parity projectors | `p_c = 0.68` (model B2) | Sec. III B, Fig. 3(b) |
| Critical exponents, model B1 | `ν = 1.85`, `γ = 0.30` | Fig. 4(b), Eq. 22 |
| Critical exponents, model B2 | `ν = 1.75`, `γ = 0.33` | Fig. 5(b) |
| Entanglement scaling exactly at `p_c` | `S_A(p_c, L_A) ~ L_A^γ`, γ≈1/3 — sub-linear, i.e. an intermediate (neither area nor volume) regime | Eq. 22-25 |
| Volume-law coefficient vanishing exponent (approach from p<p_c) | `(1-γ)ν ≈ 4/3` | Eq. 24 |
| Area-law entropy divergence exponent (approach from p>p_c) | `γν ≈ 2/3` | Eq. 25 |
| Dynamic critical exponent | `z ≈ 1` (conventional dynamic scaling, data collapse Fig. 6) | Sec. III C, Eq. 26-30 |
| Entanglement growth right at criticality (dynamics) | Sub-linear power law in time, `S_A(p_c, t≪L^z) ~ t^{γ/z}`, γ/z≈1/3 | Eq. 27, Fig. 6 |
| Entanglement velocity approaching `p_c` from below | `v_E ~ |p-p_c|^{ν(z-γ)}`, exponent ≈4/3 (vanishes → "critical slowing down") | Eq. 29 |
| Max system size (phase-transition study) | L up to 512 qubits (Clifford/stabilizer sim) | Sec. III B |
| Max system size (Zeno-phase-only study) | L up to 16 (Haar, statevector); L up to 10 (thermal entropy) | Sec. III A |
| Simulated max time | Haar sims: t=2×10²; Clifford sims: t=6×10² (entanglement already saturated within this window) | Sec. III A/B |
| Thermal entropy (mixed-state, unconditioned) | Extensive/maximal in system size ("infinite temperature") even as entanglement entropy stays area-law — striking dissociation of thermal vs entanglement entropy | Sec. III A, Fig. 2(e,f) |

## The regime boundary [paper → the crux]

**What makes entanglement bounded vs growing, precisely:** The control parameter is the
measurement rate `p` (fraction of circuit locations subjected to a projective measurement each
round, interleaved with 2-local scrambling unitaries). There is a genuine **continuous phase
transition** at a critical `p_c ∈ (0,1)`:
- `p < p_c`: **stable volume-law phase.** Crucially, this "weak measurement phase" survives *any*
  nonzero but sub-critical measurement rate — it is not immediately destroyed by measurement. The
  volume-law coefficient (entanglement-entropy density) decreases continuously with increasing `p`
  and vanishes continuously (as `(p_c-p)^{4/3}`) only exactly at `p_c`.
- `p > p_c`: **area-law "quantum Zeno phase."** The area-law entanglement value diverges as
  `p→p_c⁺` (exponent `γν≈2/3`) but stays bounded (saturating, not growing with system size) for
  any `p` strictly above `p_c`.
- `p = p_c`: an intermediate sub-linear regime, `S_A ~ L_A^{1/3}` — genuinely neither of the two
  asymptotic laws.

**Where `p=1` (maximal measurement rate) sits:** deep, robustly, in the area-law/Zeno phase for
*both* measurement-projector choices studied (Sec. III A, models A1/A2). For the rank-1 (full
Z-basis, maximally-collapsing) projector, the mechanism is airtight and **exact, not asymptotic**
(ln 447-452, 727-730): each measurement round fully projects the measured pair into a computational
product state; the following 2-local unitary can generate at most O(1) entanglement across that
link before the *next* round's measurement again disentangles it. So the entanglement is bounded
by an O(1) constant **at all times, for all L** — not merely "saturates eventually," but never
exceeds a small constant. This is the closest thing in the paper to a first-principles argument for
"a syndrome-style circuit measuring (nearly) everything every round keeps entanglement bounded."

**The GEOMETRY/STRUCTURE-dependence caveat (the load-bearing nuance for our crux):** `p_c` is
**not a single universal number** — it moves by more than a factor of 4 (0.15 → 0.68) purely from
changing *what the measurement operator resolves*, holding the unitary ensemble and 1D geometry
fixed:
- Rank-1 projectors (fully resolve both qubits in the Z basis; a maximally-informative,
  maximally-disentangling measurement) → `p_c = 0.15` — very little measurement is needed to enter
  the area-law phase.
- Rank-2/parity projectors (resolve only the joint parity `Z₁Z₂`, leaving a full qubit's worth of
  undetermined freedom per measured pair) → `p_c = 0.68` — a much higher measurement rate is needed
  before area law wins, and even at `p=1` the numerical area-law signal is weaker/less flat (Fig. 2b,d
  vs 2a,c) than the rank-1 case. The paper's own words (ln 326-331): rank-2 projectors "are expected
  to be less effective in suppressing entanglement... sometimes even generate entanglement," and if
  applied with *no interleaved unitary at all* in the `p=1` limit, they alone leave **volume-law**
  entanglement (random Page-state argument, since they don't fully collapse the local Hilbert space).

This is the key mechanism-level takeaway: **it is not "measurement rate alone" that sets the
regime — it is measurement rate combined with how much of the local Hilbert space each individual
measurement projects out (its rank/informativeness relative to the local dimension).** A "weaker"
(lower-rank-relative-to-dimension, more degenerate) measurement operator requires a much higher
rate `p` to reach the same area-law regime, and could plausibly push `p_c` arbitrarily close to (or,
for a weak enough/high-dimensional-enough projector, potentially past) 1.

**Model-class caveat (this is an ANALOGY, not an identity, to a syndrome circuit):** the transition
is established for (i) a **1D chain**, brickwork, 2-local-gate geometry (not the 2D surface-code
stabilizer geometry we care about); (ii) **Haar-random or Clifford-random local unitaries** chosen
independently at every gate location (not a fixed, deterministic, physically-structured
syndrome-extraction unitary schedule); (iii) measurements of single- or two-qubit Pauli/parity
observables directly on the evolving qubits (not weight-4 stabilizer projectors mediated through a
dedicated ancilla qubit, which is the actual object in a surface-code round). Mapping our
"p≈1 because nearly all ancillas are measured every round" onto this paper's `p` is therefore an
**analogy at the level of "what fraction of the circuit each round is measurement,"** not a
literal identification — the paper's own rank-1-vs-rank-2 result shows that this analogy is
incomplete unless the *rank/structure* of the actual stabilizer projector relative to the local
Hilbert space is also matched.

**Additional caveat: model-class dependence of whether a stable weak-measurement (volume-law)
phase exists at all.** The paper explicitly contrasts its result with Cao-Tilloy-De Luca
(Ref. [21], arXiv:1804.04638): for an **integrable** (free-fermion) system under continuous
rank-1 measurement, the entanglement entropy saturates to an area law for **arbitrarily weak**
(any nonzero) measurement rate — no stable volume-law phase exists there at all (Sec. I,
ln 49-57, 290-305). Li-Chen-Fisher attribute the difference to **chaoticity/non-integrability**:
in their non-integrable (Haar/Clifford) circuit, entanglement is carried in the "sign structure" of
an essentially random wavefunction and is much less susceptible to local measurement than the
spatially-separated EPR pairs of an integrable model, hence the transition survives to finite
`p_c>0`. **This means the qualitative existence of a volume-law phase itself depends on whether the
underlying unitary dynamics is chaotic/generic vs integrable/free** — another axis (beyond
geometry/rank) on which the "p≈1 ⇒ area law" conclusion is not automatically universal, though it
argues in the OPPOSITE direction from our worry (non-integrable models are *harder* to keep in
volume law, not easier, so it is not a caveat that would push toward growth for a generic/chaotic
syndrome circuit).

## Relevance to the d5 PEPS crux [ours]

This paper is a strong piece of supporting evidence that **"bond saturation is the expected physics
at near-maximal measurement rate" is the right qualitative prior**, but it also supplies the
sharpest available warning about **why a naive p≈1 argument is not sufficient by itself** to
guarantee our bond saturates, and gives a candidate physical culprit consistent with the pilot's
own suspicion (instrument artifact from a "compiled weight-4 √E_s POVM"):

1. **Supports bond saturation, qualitatively and rigorously, for a maximally-informative
   measurement.** The rank-1 (full-collapse) `p=1` argument is exact: a measurement that fully
   projects a local block into a product state, followed by a strictly local unitary, cannot inject
   more than O(1) entanglement before the next measurement removes it again. If our syndrome
   extraction's effective per-ancilla POVM behaves like a maximally-informative, near-full-rank
   collapse of its support, area-law/bounded-bond behavior is the generic expectation — consistent
   with treating the pilot's 4→18→>40 growth as a truncation/compilation artifact rather than
   intrinsic physics.

2. **Identifies a genuine, quantitative mechanism by which growth could be real, not an artifact:
   projector rank/informativeness relative to local dimension.** The 4.5× swing in `p_c`
   (0.15→0.68) from rank-1 to rank-2 projectors, on the *same* geometry and unitary ensemble, shows
   that "we measure ~everything every round" is not a suficient condition — what matters is how much
   of the *local* Hilbert space each individual measurement operator actually resolves. A weight-4
   stabilizer projector mediated through a single ancilla is a comparatively weak/high-degeneracy
   projector relative to the 4-data-qubit Hilbert space it acts on (much more like the rank-2/parity
   case here than the rank-1 case) — and the paper's own rank-2 model already shows both a much
   higher `p_c` *and* a visibly less-flat, less-conclusive area-law signal at `p=1` itself (Fig.
   2b,d). If the pilot's "√E_s POVM" is effectively an even weaker/more-degenerate projector than a
   clean stabilizer measurement (e.g. because of a leaky/imprecisely-compiled weight-4 operator that
   doesn't cleanly collapse the syndrome subspace), this paper's own numbers say that is exactly the
   kind of structural change that could push the effective `p_c` up toward or past our operating
   point — i.e., it is entirely consistent with, and gives a named mechanism for, "our instrument is
   injecting artifactual entanglement because it's a weaker projector than intended," rather than
   physics itself being volume-law.

3. **Does not, by itself, settle 2D/d5.** Everything numeric here is 1D brickwork with random
   (Haar/Clifford) unitaries; the paper explicitly flags dimensionality-dependence of the
   transition's critical properties as open (Discussion, ln 2667-2671: "It would be interesting to
   explore the dimensionality dependence of the critical properties"). Nothing here proves a 2D
   surface-code syndrome circuit's `p_c` — only that (a) a genuine area-law phase at high measurement
   rate is a real, established phenomenon in a closely analogous 1D setting, and (b) its location is
   structure-sensitive enough that a naive "p≈1 ⇒ done" argument should not be trusted without
   checking the actual projector structure of our compiled instrument.

**Verdict for the crux: this paper leans "our observed growth is plausibly an instrument artifact"
but supplies a concrete, falsifiable, structure-level candidate mechanism (projector rank/degeneracy
of the compiled weight-4 √E_s vs a clean ideal stabilizer projector) rather than dismissing the
growth outright.** The load-bearing next step is to check whether the compiled POVM used in the
pilot resolves the ancilla's outcome as sharply (full-rank collapse) as an ideal projective
stabilizer measurement, or whether it is closer to the paper's "rank-2/parity" case — the latter
would predict exactly the kind of slower-to-saturate, more L(and-round)-dependent bond growth the
pilot observed, and a plausible fix (tighten/re-derive the compiled projector toward full-rank
collapse, or increase effective measurement strength) rather than abandoning the area-law prior.

## How to use / trust + open questions [ours]

- **Trust level:** FULL-TEXT 精读, primary source (arXiv, this is one of the three founding papers
  of the field it defines — highly cited, foundational). The rank-1 `p=1` area-law argument
  (Sec. III A) is an *exact local argument*, not a numerical extrapolation — the highest-confidence
  claim in the note. The `p_c` values, critical exponents, and finite-size/finite-time scaling
  collapses (Figs. 3-6) are numerical (Clifford stabilizer simulation, L≤512) — solid but
  fit-quality-dependent, and explicitly *for this 1D/Clifford/random-circuit model class only*.

- **Independent-orability:** The rank-1 `p=1` bounded-entanglement claim is trivially
  independently checkable analytically (it is a 2-line argument, reproduced above). The `p_c`
  values and critical exponents would require reproducing the Clifford stabilizer simulation
  (straightforward with e.g. `stim` or a custom tableau simulator) — a cheap, high-value sanity
  check if we ever want our own 1D toy version of the measurement-rate sweep.

- **Open questions for our PEPS work:**
  1. Is our compiled weight-4 √E_s ancilla POVM, restricted to its support, closer to a rank-1
     (near-full-collapse) or rank-2/degenerate (partial-collapse) projector relative to the 4-qubit
     data-block Hilbert space it acts on? This is the single most actionable diagnostic this paper
     suggests running.
  2. Does the "entanglement entropy = log₂(bond dim needed)" identification transfer cleanly from
     this paper's exact-statevector Rényi entropy to our PEPS's *truncated* bond dimension under
     simple-update? A paper reporting the true entanglement (not a truncated proxy) is the right
     independent target to benchmark our carrier's truncation error against, once a small-system 1D
     analog is built.
  3. The paper flags the 1D→2D dimensionality dependence of the critical properties as unresolved
     (its own listed future work) — we should treat any "2D `p_c`" claim in the wider MIPT literature
     (e.g. structured/Clifford-stabilizer syndrome-circuit variants, which likely postdate this 2018
     paper) as the more directly relevant follow-up literature to chase next, rather than resting the
     final verdict on this 1D result alone.
  4. This paper's chaotic-vs-integrable contrast (point 3 above, vs Cao-Tilloy-De Luca) suggests our
     effective syndrome dynamics (a fixed, non-random, but also non-chaotic-in-the-Haar-sense
     stabilizer circuit) may not map cleanly onto EITHER studied class here — worth flagging as a
     third caveat when citing this paper's `p_c` numbers as directly predictive for our system.
