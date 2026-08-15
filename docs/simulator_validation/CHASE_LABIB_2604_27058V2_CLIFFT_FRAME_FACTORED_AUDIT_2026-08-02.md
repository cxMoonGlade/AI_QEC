# Claim audit — Chase and Labib, Clifft frame-factored exact near-Clifford simulation

## Status and decision

This packet audits arXiv:2604.27058v2 for exactly three questions: the object
Clifft represents, its exact cost law including the mechanical meaning of
"contracts during measurements", and what approximation control it does or does
not carry.  The source closes all three.  It defines the represented object
(Definition 2), proves the cost-determining structural fact (Theorem 1), states
the compile-time and sample-time cost laws (Eqs. (11)–(14)), and gives the
measured peak active dimension on its own benchmark families (Table 1).

The source is **exact and carries no approximation control at all**: no
truncation cutoff, no discarded-weight observable, no a-priori or a-posteriori
error bound appears anywhere in the 24-page artifact.  This is not an omission
to be scored against it — exactness is its design premise, and the price is that
its cost is set entirely by the peak active virtual dimension `k_max`.

The audit's decisive finding for scope purposes is Table 1's coherent-noise
family, which is a rotated surface-code memory with an `R_Z(0.02)` over-rotation
co-located with every depolarizing channel.  On that family `k_max` **grows**
with both code distance and round count — 5, 8, 13, 24 for `(d,r) =
(3,1), (3,3), (5,1), (5,5)` — and throughput falls from 19.4 M shots/s to
0.7 shots/s.  Measurement contraction is real and load-bearing (`k_max = 24` is
far below the 1045 non-Clifford operations in that circuit), but it does **not**
hold `k_max` bounded as rounds accumulate.  The source's own conclusion names
the same boundary: "Coherent-noise workloads motivate approximation schemes,
hybrid stabilizer-rank methods, and richer support for non-Pauli noise models
such as leakage."

An independent source-only reviewer checked every claim and locator against the
fixed v2 PDF, visually inspecting pages 1–8, 9–13, 17, and 20–23.  This audit
changes no implementation and grants no code permission by itself.

## Assigned closure rows

| row | exact source location | source says | source does not say | status |
|---|---|---|---|---|
| Represented object | Sec. 2.2, Definition 2, Eqs. (2)–(3), PDF p. 5 | The state is factored as a global scalar, an `N`-qubit Clifford frame `U_C`, a phase-free `N`-qubit Pauli frame, and a dense active state vector on `k = |A|` active virtual qubits tensored with `|0>` on the dormant set. | The factorization is of a pure state; no density matrix, no mixed state, and no subsystem object is defined. | closed |
| Cost-determining quantity | Sec. 2.2, Eq. (4), PDF p. 5 | `k_max = max_t |A(t)|` bounds the dominant exponential cost. | The source proves no bound on `k_max` itself in terms of circuit parameters. | closed |
| Compile-time cost | Sec. 2.6, Eq. (11), PDF p. 7 | Offline cost is `O(CN + EN + (M+T)N^2)` for `C` Clifford ops, `E` error mechanisms, `M` measurements, `T` non-Clifford rotations. | No statement about how compile time behaves when localization is adversarial. | closed |
| Sample-time cost | Sec. 2.6, Eqs. (12)–(14), PDF p. 8 | Per-shot worst case is `O((T+M+E)N + (T+M_active) 2^{k_max})`, where `M_active` counts measurements acting on the active subspace. | The `2^{k_max}` factor is not qualified by any average-case or typical-case argument. | closed |
| Expansion mechanism | Sec. 2.4 and Appendix B.1 case 2, PDF pp. 6 and 21 | A non-Clifford rotation whose localized virtual axis `v` is dormant and requires a conjugate basis promotes `v` into `A`, and `2^k -> 2^{k+1}`. | The source gives no criterion predicting how often this case fires in a given circuit family. | closed |
| Contraction mechanism | Sec. 2.4, Eqs. (8)–(9), and Appendix B.2, PDF pp. 6 and 22 | A projective measurement is localized to a single virtual observable `M_v ∈ {X_v, Z_v}`; if `v ∈ A` the shifted projector is applied to the active tensor factor, the measured axis disentangles, and `k <- k-1`; if `v ∈ D` the active state vector is unchanged. | Contraction is conditional on the localized axis lying in `A`; the source states no rate at which that condition holds. | closed |
| Noise handled in the frame | Sec. 2.4, Eq. (10), and Appendix B.3, Eqs. (23)–(24), PDF pp. 7 and 22 | Stochastic Pauli noise, feed-forward corrections, and conditional Paulis multiply into the virtual Pauli frame, leave `U_C` and `A` unchanged, and never traverse the active state vector. | Non-Pauli noise (e.g. leakage) is out of the supported model; the conclusion lists it as future work. | closed |
| Precomputability of `k_max` | Sec. 2.5, Theorem 1, PDF p. 7 | `U_C(t)` and `A(t)`, and hence `k_max`, are determined by circuit structure and localization choices, independent of error samples, measurement outcomes, and active amplitudes; they can be determined before sampling. | Theorem 1 does not bound `k_max`; it only says `k_max` is a compile-time constant of the circuit plus the chosen localization heuristic. | closed |
| Approximation control | Full-text scope; Sec. 2 in whole, Sec. 3.3, PDF pp. 3–8 and 11 | The word used throughout is "exact"; validation is by dense state-vector cross-check, mirror circuits, and Stim marginal comparison. | No truncation parameter, no cutoff, no discarded weight, no fidelity bound, and no error estimate is defined anywhere in the artifact. | closed (as absent) |
| Measured `k_max` on coherent-noise surface codes | Sec. 4.1, Table 1, PDF p. 13 | Rotated surface-code memory with `R_Z(θ=0.02)` at each depolarizing channel gives `k_max = 5, 8, 13, 24` at `(d,r) = (3,1), (3,3), (5,1), (5,5)`, with Clifft throughput 19.4 M, 1.7 M, 133.1 k and 0.7 shots/s. | The source runs no larger `d` or `r` on this family and offers no fit or extrapolation for `k_max(d, r)`. | closed |
| Benchmark circuit construction | Sec. 4.1, PDF p. 12 | The coherent-noise family is Stim's rotated memory experiment at `p = 10^-3` with an `R_Z(θ)` over-rotation, `θ = 0.02`, co-located with each depolarizing channel; adapted from Ref. [38]. | The rotation is single-qubit `R_Z`; no two-qubit coherent generator is benchmarked. | closed |
| Mid-circuit measurement and reset support | Sec. 3.1 stage 1, PDF p. 9 | "Nearly all of Stim's existing noise channels, mid-circuit measurements, detectors, observables, and repeat blocks are supported without modification." | The word "nearly" is not resolved in the artifact; the exact excluded set is deferred to the documentation and codebase [48]. | partial |
| Extractable quantum-state information | Sec. 3.3 and Appendix C, PDF pp. 11 and 23 | Two routes exist: dense expansion of the factored state `|ψ> = γ U_C P̃ |φ>_A` into a computational-basis state vector "for sufficiently small circuits", and a Clifft-native expectation-value probe used to evaluate `<Y_L>` after decoder correction. | No reduced density matrix, no partial trace, no subsystem state, and no distance between two states is defined or computed. | closed (as absent) |
| Released implementation | Title-page footer and Sec. 1, PDF pp. 1–2; Refs. [48], [49], PDF p. 20 | `https://github.com/unitaryfoundation/clifft`, Apache 2.0, distributed as `clifft` on PyPI, with a companion `clifft-paper` repository for circuits, scripts and raw data. | The paper states no commit, tag, or version for either repository. | closed |
| Tensor-network content | Full-text scope, Secs. 1–3 | Tensor-network and MPS methods are cited only as an alternative class in the introduction, PDF p. 1. | Clifft contains no tensor network, no bond dimension, and no MPS/PEPS object. | closed (as absent) |
| Bound on `k_max` for a circuit family | Full-text scope | Table 1 reports measured `k_max` values. | No theorem, no a-priori bound, and no per-instance certificate on `k_max` is proved anywhere. | missing |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Physical active operation `O` at time `t` | Conjugate its Pauli generator through the cumulative Clifford frame, `P̃_O = (U_C^{(t)})† P_O U_C^{(t)}` | Active operations are generated by Pauli operators, so the image is a Pauli string | Virtual Pauli generator `P̃_O` | Sec. 2.1, Definition 1, Eq. (1), PDF p. 4 | complete |
| Non-identity `N`-qubit virtual Pauli `P̃_O` | Greedy CNOT/CZ elimination: pivot on a qubit with `x_v = 1`, clear `X`-support with `CNOT_{v→q}`, clear residual `Z`-support with `CZ_{v,q}`; pure `Z`-strings use `CNOT_{q→v}` | Support is erased monotonically and never respreads to cleared qubits | `V P̃_O V† = α P_v` on one virtual qubit, with `|V| ≤ 2N` gates | Lemma 1, PDF p. 5; Appendix A, Eqs. (15)–(17), PDF pp. 20–21 | complete |
| Localized rotation `exp(-iθ α P_v)` and frame `P̃` | Absorb `V†` into `U_C`, conjugate the Pauli frame `P̃ <- V P̃ V†`, commute the rotation past `P̃` picking up a sign `(-1)^c` | `V` chosen to act trivially on `|0>_D` where possible (Lemma 2, Eq. (7)) | Either a scalar into `γ`, or `k <- k+1` with `|φ>_A <- |φ>_A ⊗ |+>`, or an in-place phase on an active factor | Eq. (6), PDF p. 6; Appendix B.1, Eqs. (18)–(19), PDF p. 21 | complete |
| Projective measurement with outcome `m` | Localize to `M_v`, commute the projector past the Pauli frame to get the parity shift `Π_m P̃ = P̃ Π_{m⊕p}`, then apply | The measured axis `v` is either dormant or active; the branch is chosen by the outcome | `v ∈ D`: deterministic or uniformly random, active vector unchanged. `v ∈ A`: amplitudes masked or folded, axis disentangled and demoted, `k <- k-1` | Eqs. (8)–(9), PDF p. 6; Appendix B.2, Eqs. (20)–(22), PDF p. 22 | complete |
| Conditional physical Pauli `E^c` | Heisenberg map to `Ẽ`, multiply into the frame `P̃ <- Ẽ^c P̃`, accumulate the phase into `γ` | The `N`-qubit Pauli group is closed under multiplication | New phase-free frame `P̃^{(t+1)}`; `U_C`, `A` and `|φ>_A` unchanged | Eq. (10), PDF p. 7; Appendix B.3, Eqs. (23)–(24), PDF p. 22 | complete |
| Compiled circuit | Resolve all Clifford absorption, Heisenberg mapping and localization ahead of time; emit bytecode with a fixed active-set schedule | Theorem 1: the trajectory of `U_C` and `A` is independent of samples, outcomes and amplitudes | `k_max` known before sampling; SVM allocates a `2^{k_max}` array once and reuses it per shot | Theorem 1, PDF p. 7; Sec. 3.2, PDF p. 10 | complete |
| Rotated surface-code memory, `d ∈ {3,5}`, `r ∈ {1,3,5}`, `R_Z(0.02)` at each depolarizing site | Compile and sample under the above pipeline | Stim rotated memory generator, `p = 10^-3`, 16 physical CPU cores | `k_max = 5, 8, 13, 24`; 19.4 M, 1.7 M, 133.1 k, 0.7 shots/s | Sec. 4.1, PDF p. 12; Table 1, PDF p. 13 | complete at source-claim level |

## What this audit does not close

1. **No `k_max` law.**  Table 1 gives four measured points on the coherent-noise
   family and no functional form.  Any statement of the shape "`k_max` grows
   linearly in rounds" is an extrapolation from four points, not a source claim.
2. **The "nearly all" instruction set.**  Sec. 3.1 defers the exact supported
   instruction list to the documentation and codebase.  Whether `R`, `RX`, `MR`
   and `MRX` reset instructions are among the supported set cannot be settled
   from the artifact and must be read from the pinned repository.
3. **No repository ref.**  The paper names two GitHub URLs and a PyPI package
   but no commit, so nothing in this audit binds a specific state of the code.
4. **Localization heuristic dependence.**  Theorem 1 makes `k_max` a function of
   the circuit *and the localization choices*.  The greedy Appendix-A algorithm
   is one choice; the conclusion states that better heuristics "may reduce
   `k_max`".  The Table 1 values are therefore properties of this implementation,
   not lower bounds for the frame-factored representation as such.
