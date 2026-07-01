# Full-text review — Rivas, Huelga, Plenio, "Entanglement and non-Markovianity of quantum evolutions" (arXiv:0911.4270, PRL 105, 050403 (2010))

> **Provenance (2026-07-01): FULL-TEXT read (精读).** PDF `arxiv.org/pdf/0911.4270` → txt
> `outputs/papers/0911.4270.txt` (PyMuPDF, 5 pages, arXiv v2 28 Jul 2010). All Eq/Fig refs from that
> text. The comprehensive review is Rivas–Huelga–Plenio, RPP 77, 094001 (2014), arXiv:1405.0303
> (cached `outputs/papers/1405.0303.txt`).

## Metadata [paper]
- **Authors.** Ángel Rivas, Susana F. Huelga, Martin B. Plenio (Ulm / Hertfordshire / Imperial).
- **Venue.** arXiv:0911.4270v2; **Phys. Rev. Lett. 105, 050403 (2010)**. The canonical "RHP measure".
- **Type.** Theory: two non-Markovianity measures, one entanglement-based (sufficient), one
  CP-divisibility-based (necessary+sufficient given the map).

## Executive summary [paper]
Defines Markovianity as **CP-divisibility**: `E(t2,t0)=E(t2,t1)E(t1,t0)` with the intermediate map
`E(t2,t1)` **completely positive** (Eq. 2, the quantum Chapman–Kolmogorov). Two measures of the
deviation: (1) **I(E)** — a **sufficient** witness needing no model: entangle the system with a
shielded ancilla; local CPT maps cannot increase entanglement, so Markovian ⇒ system–ancilla
entanglement decays monotonically; any temporary increase certifies non-Markovianity. (2) **The
CP-divisibility measure** (necessary+sufficient given the dynamical map): integrate the
**non-complete-positivity of the intermediate map**, detected via the Choi state's trace norm.
Neither requires an optimization.

## Method (deep) — the exact definitions [paper]
- **CP-divisibility = Markovian** [Eq. 2]. Time-dependent Lindblad with `γ_k(t)≥0` ⟺ all
  intermediate `E(t2,t1)` CP.
- **Entanglement measure (sufficient, model-free).** Maximally entangled `|Φ⟩=1/√d Σ_n|n⟩|n⟩`,
  `ρ_SA(0)=|Φ⟩⟨Φ|`, local bath on S. Measure
  `I(E) = ∫_{t0}^{tmax} |dE[ρ_SA(t)]/dt| dt − ∆E` (with `∆E=E[ρ_SA(t0)]−E[ρ_SA(tmax)]`) — the total
  entanglement backflow; `I(E)=0` if `E[ρ_SA(t)]` is monotone (Markovian). `E` = **logarithmic
  negativity** `E_N=log2‖ρ^{T_A}‖_1` in the Gaussian example. `I(E)>0` ⇒ non-Markovian (sufficient,
  may miss some).
- **CP-divisibility measure (necessary + sufficient).** Split `E(t+ε,0)=E(t+ε,t)E(t,0)` [Eq. 3];
  extract `E(t+ε,t)=E(t+ε,0)E(t,0)^{-1}` (where invertible). Non-CP witness via Choi:
  `f_NCP(t+ε,t)=‖(E(t+ε,t)⊗1)(|Φ⟩⟨Φ|)‖_1`; `=1` iff CP, else `>1`.
  `g(t)=lim_{ε→0+}[f_NCP(t+ε,t)−1]/ε ≥ 0`, `g=0` iff `E(t+ε,t)` CP. **THE MEASURE:**
  `I = ∫₀^∞ g(t) dt`; normalized `D_NM = I/(I+1) ∈ [0,1)`.
- **PURE DEPHASING closed form** [Eq. 4]: for `dρ/dt=γ(t)(σ_z ρ σ_z − ρ)`,
  `g(t)=0` for `γ(t)≥0`, `g(t)=−2γ(t)` for `γ(t)<0`, hence
  **`I = −2 ∫_{γ(t)<0} γ(t) dt`** = twice the area of the rate below zero (→∞ if the negative rate
  ~`tan`, the BLP central-spin example).

## Limitations [paper]
- The necessary+sufficient measure needs the **dynamical map** (process tomography or a model) AND
  `E(t,0)` invertible (singularities where `E(t,0)` is non-invertible leave `E(t+ε,t)` undefined —
  a consequence of tracing out the environment).
- `I(E)` (entanglement) is only **sufficient** — some non-Markovian evolutions are undetected.
- CP-divisibility (RHP) is **strictly finer** than trace-distance backflow (BLP): RHP>0 ⇒ some pair
  MAY show backflow, but a P-divisible-but-not-CP-divisible map can have RHP>0 with BLP=0.

## Relevance to qec_twin [ours]
**RHP `I` is the field-standard CP-divisibility quantifier for the coupled-teacher SOURCE/WEDGE
layer** — the sharpest "CP-divisibility breaking" reading of the wedge
(`project-coupling-nonmarkovian-is-the-contribution`: the wedge = CP-divisibility breaking). Mapping
to the pilot (`outputs/coupled_pseudomode_pilot_v1_n2.py`, pure dephasing, single Lorentzian):
- The pilot's TCL dephasing rate is `γ(t) ∝ Γ_R'(t) = ∫₀ᵗ Re C(τ)dτ` (from `Γ_R(t)=∫₀ᵗ(t−τ)Re C dτ`).
  `γ(t)<0` ⇔ `Γ_R` decreasing ⇔ coherence revival.
- **`I = −2∫_{γ<0} γ dt` = 2 × the total downward excursion of `Γ_R` = 2 × my ΔΓ metric** (the
  "max drop of Γ below its running max", generalized to sum all dips) — 0.14 @γ=0.15, 0.36 @γ=0.05
  in `outputs/coupled_pseudomode_pilot_v1_revival_robustness.py`. So the pilot's ΔΓ IS (½ of) the
  RHP measure.
- **Operate it:** pure-dephasing → Eq. 4 directly from the TCL rate. General/matrix case → reconstruct
  `E(t+ε,t)` on a small window, compute `f_NCP` from the Choi trace norm (reuses the ledgered
  `D_Choi` machinery), integrate `g(t)`.

## How to trust + open questions [ours]
- **Trust:** FULL-text 精读; equations verbatim. Peer-reviewed (PRL 105, 050403); canonical, reviewed
  in RPP 77, 094001 (2014).
- **BLP vs RHP (ours):** use BOTH — BLP (trace-distance backflow, `[[blp_nonmarkovianity_measure_0908.0238]]`)
  is model-free / experiment-friendly and is the observable-side witness; RHP (CP-divisibility) is the
  finer generator-side quantifier and the exact "CP-divisibility breaking" the wedge claims. For the
  pilot's single-Lorentzian pure dephasing they coincide up to convention; on the matrix-BCF /
  multi-qubit / non-dephasing case they can differ ⇒ report both, and note which is being claimed.
- **Open:** RHP needs the reconstructed intermediate map (invertibility) — a real cost at multi-qubit;
  the pilot's closed-form γ(t) sidesteps it only because pure dephasing is exactly solvable.

## Provenance line
Downloaded 2026-07-01 from arXiv (0911.4270 → PyMuPDF txt, 5 pp). PRL 105, 050403 (2010). Full-text
精读; figures = captions + in-text numbers. Review context: 1405.0303 (RPP 2014).
