# Pleasance–Neira–Merkli–Petruccione NJP 27 114514 — collision-order and CCM source audit

Status: source-only audit for the GCAPEPS finite-memory fixture-v2 delta-closure, 2026-08-01.

Artifact: version-of-record open-access PDF, DOI 10.1088/1367-2630/ae1b31, published
13 November 2025, downloaded from IOP 2026-08-01. PDF pages cited below are artifact
pages 1–21; the printed article page is artifact page minus one.

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| order/schedule dependence of non-Markovianity | Abstract, PDF p. 2; Sec. 4.3, Eqs. (41)–(42), PDF p. 13 | For the all-qubit CM with U = e^(−iτ σx⊗σx), W = e^(−iε σz⊗σz): when AA entanglement precedes the SA collision, non-Markovian behavior emerges for suitable (ε, τ); when SA collisions precede AA entanglement, D′(n) = e^(−2iτ)(cos 2τ − i sin 2τ cos 2ε)^(n−1) and \|D′(n)\| never increases, so the dynamics is Markovian **for all** τ, ε. | It does not treat a deterministic every-other-round exchange schedule, a 2×w ladder, stochastic event masks, or any tensor-network carrier. | closed |
| composite-CM mapping (Markovian embedding) | Theorem 1, Eqs. (9)–(10), PDF p. 5; Prop. 1, Eq. (13), PDF p. 6; Sec. 3.1 | The reduced dynamics of the correlated-ancilla CM is the reduction of the n-th power of one CPTP map M on the enlarged system S + (L−1) ancillas; the enlarged dimension grows as dim(H_S)·d^(L−1), so the embedding is practical only for small L; the L−1 ancillas are the memory part, the rest non-memory. | It does not bound any tensor-network bond dimension and does not identify the embedding with Campbell et al.'s CCM: the map M′ (Eq. (14)) differs in operation order and in which part S collides with. | closed |
| AA entanglement necessary | Eq. (33) and Fig. 6 discussion, PDF p. 11; Conclusions, PDF p. 13 | At ε = π/4 the concurrence of every interacting pair beyond the first vanishes (which the source states may be interpreted as an effect of entanglement monogamy) and D(n) = (cos 2τ)^n is strictly nonincreasing: all non-Markovianity is eliminated; conclusions state AA entanglement within the interacting portion is "necessary (although not sufficient)". | Necessity is established for this all-qubit model class, not as a universal theorem for every environment structure. | closed at the model scope |
| backflow requires correlations | Eqs. (35)–(39), PDF pp. 11–12 | The trace-distance increase between collisions n and m is bounded by I_SAn(n): total S–An correlations plus distinguishability of the reduced ancilla states, both evaluated immediately before the n-th collision; a nonmonotonic increase can occur only if those are nonzero. | The bound is an upper bound (citing Laine–Piilo–Breuer EPL 92 60010); it does not by itself predict the magnitude of any specific revival. | closed |
| commuting-W no-go | Remark and Eq. (8), PDF p. 5 | If the correlation-generating operation W commutes with the S–A interaction U, the intra-environment correlations drop out of the reduced dynamics entirely. | It does not quantify partial non-commutation. | closed |
| non-monotone parameter dependence | Fig. 4, PDF p. 9; Eq. (30), PDF p. 10; Eq. (40), PDF p. 13 | N_BLP over (ε, τ) has interior maxima (ε ≈ 0.195π; τ ≈ 0.15π, 0.35π), vanishes on lines ε ∈ {0, π/4, π/2} and τ ∈ {0, π/4, π/2}; at τ = π/4, D(n) = e^(−iπn/2) cos 2ε is Markovian regardless of ε. | No monotone law in coupling strength is stated anywhere; the dependence is explicitly non-monotone with interior maxima. | closed |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| ρ_S(0), ancillas ρ_A^⊗(n+L−1) | apply W_[L,1], …, W_[n+L−1,n] then interleave U_Sj per Eq. (6); trace ancillas | unitary (or CPTP) U, W; fixed ρ_A | ρ_S(n) = Λ_n[ρ_S(0)] (Eq. (7)) | Sec. 3, Eqs. (5)–(7), PDF p. 5 | complete |
| ϑ on S + (L−1) ancillas | M[ϑ] = Tr_{A1}(U_S1 W_[L,1] (ϑ ⊗ ρ_A)) | Theorem 1 proof via the auxiliary map (44)–(46) | ρ_S(n) = Tr M^n[ρ_S(0) ⊗ ρ_A^⊗(L−1)] | Thm 1, Eqs. (9)–(10), proof Sec. 6.1, PDF pp. 5, 14 | complete |
| all-qubit case, ρ_A = \|+⟩⟨+\| | Liouville 16×16 representation; D(n) = Σ_m [(cos2τ A1 − i sin2τ A2)^n]_{0m} ρ_m | Prop. 2; block-circulant diagonalization | decoherence function D(n) | Prop. 2, Eqs. (20)–(21), proof Sec. 6.3, PDF pp. 8, 15–18 | complete |
| reversed order | M′[ϑ] = Tr_{A1}(W′ U_S1 …) per Eq. (41) | Sec. 6.5 matrices B1, B2 | D′(n) = e^(−2iτ)(cos 2τ − i sin 2τ cos 2ε)^(n−1), \|D′(n)\| nonincreasing | Eqs. (41)–(42), (91)–(95), PDF pp. 13, 19 | complete |
| trace-distance witness | D(ρ1, ρ2) = ½‖ρ1 − ρ2‖₁; N_BLP sums positive increments, maximized over antipodal pairs via η | BLP measure [56, 57]; Eq. (27) makes S₊ state-independent here | witness condition \|D(n+1)\| > \|D(n)\| | Eqs. (23)–(29), PDF pp. 8–9 | complete |

## Project application

The fixture-v2 (X8) delta adds a deterministic intermittent cross-row CX exchange to
the v1 persistent-memory dilation. This source supplies the closest published
schedule-dependence class: in an all-qubit collision model with the same primitive
family (Pauli-product exponentials), whether the entangling operation acts before or
after the system collision decides Markovian versus non-Markovian outright
(order: Eqs. (41)–(42); necessity: Eq. (33)). It also supplies the mechanism-level bound (Eqs. (35)–(36)) that
backflow requires correlations between the system and the interacting portion of
the environment. Both are **adjacent grounding**: the v2 ladder is not this model
(persistent 2×w memory, stochastic masks, deterministic every-other-round CX, no
fresh-ancilla stream), and no quantitative curve transfers. The v2 measured
interaction effect (persistent CX destroys the fixed-pair witness; intermittent CX
plus reduced collision density produces it) remains a registered project hypothesis;
this source establishes that order/schedule sensitivity of exactly this kind exists
in published collision models and that no monotone coupling-dependence law is
available to contradict it. The commuting-W remark (Eq. (8)) is a design no-go the
v2 emitter must respect: a cross-row Clifford layer that commuted with the collision
rotations would provably change nothing about the reduced dynamics.

## Competing evidence and kill conditions

- Eq. (42) is derived for the fresh-ancilla stream with ρ_A = \|+⟩⟨+\| (Sec. 6.5
  sets ρ1 = 1); it must not be quoted as covering the v2 ladder's retained memory.
- The necessity claim is model-scoped; treating it as a universal theorem would be
  an over-claim and must fail review.
- Footnote 5 (PDF p. 7): the memory-depth conventions of this paper and of
  Campbell et al. differ by one; any cross-citation must state which convention.
- If a v2 measurement shows backflow with provably zero S–memory correlations
  before the revival round, that contradicts the Eq. (35)–(36) reading and reopens
  this row.

## Source-local verdict

- read_status: complete
- evidence_status: persisted
- assigned-row status: closed for order dependence, CCM embedding, necessity at
  model scope, the correlation bound, the commuting-W no-go, and non-monotone
  parameter dependence.
