# Full-text review — Breuer, Laine, Piilo, "Measure for the degree of non-Markovian behavior of quantum processes in open systems" (arXiv:0908.0238, PRL 103, 210401 (2009))

> **Provenance (2026-07-01): FULL-TEXT read (精读).** PDF `arxiv.org/pdf/0908.0238` → txt
> `outputs/papers/0908.0238.txt` (PyMuPDF, 4 pages, arXiv v2 5 Jan 2010). All Eq/Fig refs from that
> text. **NOTE (theory-first catch):** the id 0907.3968 that was first tried is a DIFFERENT paper
> (stochastic resonance); the correct BLP id is **0908.0238**. PDF pp. 2–3 were rendered and visually
> inspected on 2026-07-13 for Eqs. (5), (9)–(13) and the one-way divisibility implication.

## Metadata [paper]
- **Authors.** Heinz-Peter Breuer (Freiburg); Elsi-Mari Laine, Jyrki Piilo (Turku).
- **Venue.** arXiv:0908.0238v2 [quant-ph]; **Phys. Rev. Lett. 103, 210401 (2009)**. The canonical
  "BLP measure" reference.
- **Type.** Theory: constructs THE trace-distance / information-backflow non-Markovianity measure.

## Executive summary [paper]
Defines quantum non-Markovianity via **information backflow**, measured by the **trace distance**
`D(ρ1,ρ2)=½tr|ρ1−ρ2|` (state distinguishability). Every CPT (indeed every positive-TP) map is a
**contraction** of `D` (Eq. 2), so any **divisible** dynamics — a dynamical semigroup, OR a
time-dependent Lindblad generator with **all rates γ_i(t) ≥ 0** — makes `D(ρ1(t),ρ2(t))`
**monotonically non-increasing** for every initial pair (Eq. 5). In the paper's information-backflow
definition, a process is BLP-non-Markovian when `D` increases at some time for some pair. This is a
sufficient witness of nondivisibility, but absence of BLP backflow is not equivalent to general
CP-divisibility. The degree is the total backflow, maximized over initial pairs.

## Method (deep) — the exact definitions [paper]
- **Trace distance** [Eq. 1]: `D(ρ1,ρ2)=½ tr|ρ1−ρ2|`, `0≤D≤1`; `½[1+D]` = optimal one-shot
  distinguishing probability (Helstrom).
- **Contraction** [Eq. 2]: `D(Φρ1,Φρ2) ≤ D(ρ1,ρ2)` for all CPT (and positive-TP) `Φ`.
- **Divisibility** [Eq. 9]: `Φ(τ+t,0)=Φ(τ+t,t)Φ(t,0)` with the intermediate `Φ(τ+t,t)` also CPT.
  Time-dependent Lindblad [Eq. 7] `K(t)ρ=−i[H(t),ρ]+Σ_i γ_i(t)(A_i ρ A_i† −½{A_i†A_i,ρ})` with
  `γ_i(t)≥0` ⇒ divisible ⇒ Eq. 5: `D(ρ1(τ+t),ρ2(τ+t)) ≤ D(ρ1(t),ρ2(t))`.
- **Rate** [Eq. 10]: `σ(t,ρ1,2(0)) = d/dt D(ρ1(t),ρ2(t))`. Divisible ⇒ `σ≤0` ∀t, ∀pair.
- **BLP-non-Markovian** ⇔ ∃ pair `ρ1,2(0)` and time `t` with `σ>0`.
- **THE MEASURE** [Eq. 11]:
  `N(Φ) = max_{ρ1,2(0)} ∫_{σ>0} dt σ(t,ρ1,2(0))`
  = [Eq. 12] `max_{ρ1,2(0)} Σ_i [ D(ρ1(b_i),ρ2(b_i)) − D(ρ1(a_i),ρ2(a_i)) ]` over the intervals
  `(a_i,b_i)` where `σ>0`. Divisible dynamics imply `N(Φ)=0`, and `N>0` witnesses
  nondivisibility. The reverse implication `N=0 ⇒` CP-divisible does not hold in general.

## Worked examples — DIRECTLY our regime [paper]
1. **Damped Jaynes–Cummings, Lorentzian J(ω), weak coupling γ0/λ=0.01, detuning ∆.** Single Lindblad
   `A=σ−`, time-dependent rate `γ(t)`. For the optimal pair `ρ1(0)=|+⟩⟨+|`, `ρ2(0)=|−⟩⟨−|`
   [Eq. 13]: `σ(t)=−γ(t) exp[−Γ(t)]`, `Γ(t)=∫₀ᵗ γ(t')dt' ≥0` (CP of Φ(t) preserved). **γ(t)<0
   (negative rate) ⇔ σ>0 ⇔ trace-distance increase = "revival of the coherence."** This links
   negative rates, divisibility violation, and coherence revival in one line.
2. **Central spin + N-spin bath, PURE DEPHASING** `H=A Σ_k σ_z σ_z^{(k)}`: coherences ×`f(t)=cos^N(2At)`;
   trace distance [Eq. 14] `D=√(a²+f²|b|²)`, `a`=population diff, `b`=coherence diff.
   **Optimal pair = σx eigenstates (a=0, |b|=1)** → `D=f(t)=|cos^N(2At)|` oscillates 0↔1 → the sum
   Eq. 12 diverges → `N(Φ)=+∞`; formal master eq `H=0, A=σz, γ(t)=AN tan(2At)` (negative-rate
   dephasing). **This is exactly the pilot's pure-dephasing coherence-revival wedge.**

## Limitations [paper]
- Exact `N` requires the full reduced dynamics + a maximization over initial pairs (hard in high dim);
  BUT **any observed growth of `D` is already a lower bound + a sufficient witness** of
  non-Markovianity (Eq. 5 is only-if for divisible). No environment model needed → experiment-friendly.
- `N` is a trace-distance functional; it does not by itself decompose *which* coherence revives.

## Relevance to qec_twin [ours]
**BLP `N(Φ)` is the field-standard scalar for the coupled-teacher SOURCE/WEDGE layer** (the
coherence-revival / information-backflow signature; `project-nonmarkovian-wedge-must-be-coherence`).
Mapping to the pilot (`outputs/coupled_pseudomode_pilot_v1_n2.py`, pure dephasing):
- The pilot's coherence factor is `exp(−Γ_R(t))`, `Γ_R(t)=∫₀ᵗ(t−τ)Re C(τ)dτ`. For the σx-eigenstate
  pair on a dephased qubit, `D(t)=exp(−Γ_R(t))` (a=0,|b|=1), so `σ(t)=−Γ_R'(t)exp(−Γ_R)` and
  `Γ_R'(t)=∫₀ᵗ Re C(τ)dτ` is the TCL dephasing rate. `Γ_R'<0` ⇔ revival ⇔ `σ>0`.
- **`N(Φ)` = the total upward excursion of `D(t)` = the SUM of the pilot's `|ρ|`-revival amplitudes**
  — the "true trough→peak amplitude" my robustness sweep already prints (0.024 @γ=0.15,
  0.106 @γ=0.05). So the pilot's wedge amplitude IS (a lower bound to) the BLP measure.
- **Operate it:** evolve the reduced ρ(t) for the maximizing pair (σx eigenstates for dephasing; a
  random-pair search otherwise), form `D(t)=½tr|ρ1(t)−ρ2(t)|`, sum the positive-`σ` excursions
  (Eq. 12). No optimization needed beyond the pair search; for dephasing the optimum is known.

## How to trust + open questions [ours]
- **Trust:** FULL-text 精读; all equations verbatim. Peer-reviewed (PRL 103, 210401), THE canonical
  non-Markovianity measure (>thousands of citations); reviewed comprehensively in Rivas–Huelga–Plenio
  RPP 77, 094001 (2014) (arXiv:1405.0303, cached `outputs/papers/1405.0303.txt`).
- **Open (ours):** (1) BLP is a NECESSARY signature but does not by itself establish decode-relevance —
  that is the decoder layer (%ΔLER). (2) BLP and RHP can disagree in general (RHP CP-divisibility is
  strictly finer than BLP P-divisibility/backflow); for the pilot's single-Lorentzian pure dephasing
  they coincide up to the convention factor. (3) Maximization over pairs is trivial for dephasing;
  for the matrix-BCF multi-qubit case the pair search must be redone.

## Provenance line
Downloaded 2026-07-01 from arXiv (0908.0238 → PyMuPDF txt, 4 pp). PRL 103, 210401 (2009). Full-text
精读; figures = captions + in-text numbers.
