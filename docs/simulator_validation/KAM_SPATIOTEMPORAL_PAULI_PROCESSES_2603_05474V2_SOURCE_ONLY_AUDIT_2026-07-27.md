# Source-only claim audit — Kam et al., arXiv:2603.05474v2

Date: 2026-07-27

Packet status: `draft_pending_independent_source_only_review`

Source artifact: `docs/papers/2603.05474v2.pdf`

Pinned source URI: `https://arxiv.org/abs/2603.05474v2`

Source PDF SHA-256:
`3929443fb4587fefdd675dd611e05c9ce41ec4d8d0aea774bc8efb8bb0407c80`

Fresh layout text: `docs/papers/2603.05474v2.txt`

Fresh layout text SHA-256:
`45ee7ac7cb5f16b9a83d371d8fd8bb1bd185fa40fd3ecb80c1fdb6a58fd9e49e`

Provenance packet: `docs/papers/2603.05474v2.provenance.json`

Provenance packet SHA-256:
`2573431bb9516c9190f2171d0b75d0fc88b7eb4c5f538dffa48160a9641e95e6`

Read status: `complete`

Evidence status: `persisted`

Independent review status: `pending`

The complete 54-page PDF was read in source order, including Appendices A--C,
all captions, Data and Code Availability, and the references. Text extraction
was used for traversal only. The following load-bearing pages were rendered and
visually checked at symbol, equation, figure, axis, caption, and version fidelity:
PDF pp. 1, 9--10, 15--21, 24--41, and 48--54.

This packet is source-only. Project interpretation appears in separate sections
and is explicitly labelled. The source's SPP PEPS is a classical tensor network
over Pauli-trajectory weights; it is not the repository's quantum residual
state in the invariant \(\lvert\psi\rangle=C\lvert\phi\rangle\).

## Bounded source verdict

The paper establishes an operationally twirled, multi-time Pauli process from a
general process tensor. The twirled Choi object is process-separable and is
equivalent to a joint probability distribution over Pauli trajectories. Local
physical-leg contractions turn a process-tensor MPO/PEPO into an SPP MPS/PEPS,
and temporal SPP bonds do not exceed the corresponding environment/process
bonds. Suitable nonnegative row-stochastic SPP MPS gauges admit finite-state
HMM realizations.

The QEC studies then use SPPs as generative Pauli-fault models. They do not
simulate the untwirled coherent circuit alongside the twirled process, do not
represent post-measurement conditional quantum states, and do not define a
measurement--reset transaction or a raw-syndrome-to-detector/observable Record
fold. The SPP trajectory probability is a noise-path probability, not a Born
mass ledger over syndrome-measurement histories.

For CAPEPS, the source is load bearing in two directions:

1. A valid twirled baseline should retain the source's possible classical
   correlations across space and time. An i.i.d. tableau baseline is a narrower
   model unless that restriction is deliberately frozen.
2. The source's PEPS language must not be conflated with a quantum-state PEPS
   residual. It encodes classical Pauli trajectory weights after twirling.

The source does not establish CAPEPS correctness, CAPEPS efficiency, or a
matched CAPEPS/full-PEPS resource advantage.

## Assigned closure rows

| load-bearing row | exact source location | source says | source does not say | status |
|---|---|---|---|---|
| general multi-time process and instrument slots | PDF pp. 9--11, Eqs. (8)--(17) | A process tensor is multilinear in an input state and an ordered sequence of CP interventions; its Choi representation obeys positivity and recursive causal constraints. A QEC syndrome-extraction cycle may be chosen as one coarse instrument. | This general formalism is not itself a concrete syndrome-measurement/reset implementation. | `closed` at general process-tensor scope |
| multi-time Pauli twirl | PDF pp. 15--16, Definition 4.1, Eq. (32), Proposition 4.2 | Independent Pauli twirls act on every input-output time pair and form a valid, idempotent, causality-preserving superprocess. | It does not say the untwirled microscopic process is unchanged. | `closed` |
| process-separable joint Pauli law | PDF p. 16, Theorem 4.3 and Definition 4.4, Eqs. (33)--(36); PDF pp. 48--49, Appendix B | The twirled process is diagonal in a product Bell/Pauli-Choi basis and admits nonnegative normalized weights over full spatiotemporal Pauli trajectories. | These weights are Pauli-noise paths, not syndrome-measurement branch masses or conditional states. | `closed` |
| operational meaning of the twirl | PDF p. 17, paragraphs after Eqs. (36)--(37); PDF p. 29, Sec. 6.1 | Under the assumed Pauli-frame randomisation/randomised-compiling protocol, the SPP is an effective process that reproduces the relevant Pauli-basis/stabilizer-QEC statistics. The paper explicitly says this does not literally transform the microscopic dynamics. | It gives no general equality between an unrandomized coherent circuit and its SPP. | `closed` with different-channel/protocol boundary |
| local tensor-network map | PDF pp. 18--20, Proposition 4.5, Definition 4.6, Lemma 4.7, Corollary 4.8, Eqs. (39)--(48), Figs. 3--4 | Fixed contractions on open physical legs produce an SPP MPS/PEPS; temporal bonds are unchanged by the local map and are bounded by the process/environment Liouville bond. | The paper does not prove generic efficient contraction of the resulting 2D PEPS or bound its spatial truncation error. | `closed` for representation and temporal-bond bound only |
| transfer/HMM structure | PDF pp. 24--28, Eqs. (55)--(75), Proposition 5.3 | Under time-homogeneous ergodic assumptions, transfer spectra control asymptotic correlations. A nonnegative row-stochastic gauge is sufficient for an edge-emitting HMM with the same bond dimension. | The sufficient HMM condition is not necessary, and a same-dimension HMM is not guaranteed for a generic SPP MPS. | `closed` |
| temporal-storm QEC workload | PDF pp. 29--33, Eqs. (76)--(81), Figs. 8--10 | The numerical model combines independent within-round gate noise with one additional SPP-sampled Pauli fault per data/ancilla qubit at each round, fixes marginal rate \(p=0.1\%\), sweeps correlation length, samples with Stim, and decodes with a marginally matched MWPM model. | It is not a coherent non-Pauli XZZX circuit and the decoder does not exploit the correlations. | `closed` for the printed rotated-surface-code workload |
| temporal-correlation result | PDF pp. 32--33, Figs. 9--10 | Across the selected memory and stability experiments, longer temporal correlations worsen the reported logical performance and weaken the fitted distance/timelike suppression at fixed marginals. | It is not a universal threshold theorem and is partly a decoder-mismatch result. | `closed` for the selected empirical sweep |
| QCA-to-PCA mapping | PDF pp. 34--37, Eqs. (82)--(93); PDF pp. 49--54, Appendix C | Under classical bath initialization, the controlled-unitary orthogonality assumption, and a per-cycle system Pauli twirl, the bath is re-classicalized and the coherent QCA yields a two-sublattice PCA with flip probability \(\sin^2(k\theta)\), plus conditional Pauli emissions. | This is not an untwirled coherent system-state simulator and does not preserve discarded quantum temporal correlations. | `closed` under the stated assumptions |
| pseudo-critical bath result | PDF pp. 37--38, Fig. 11 and Eq. (95) | For the printed finite lattices and parameters, the density crossover, scaled-variance peak, and fitted correlation-time peak identify a narrow pseudo-critical region near \(0.39\pi\). | It is not a thermodynamic critical-point proof; the source itself uses pseudo-critical/critical-like language and notes possible non-single-exponential decay. | `closed` as finite-size empirical evidence |
| QCA surface-code breakdown | PDF pp. 39--40, Fig. 12 | In the selected SPP/PCA workload, reported distance scaling degrades and reverses beyond the estimated pseudo-critical threshold; MWPM uses numerically estimated marginal detector rates and ignores correlations. | It is not evidence that every decoder or every coherent pre-twirl circuit has the same failure law. | `closed` for the selected empirical workload |
| complete CAPEPS raw/Record law | complete source scope, represented by PDF pp. 15--20 and 29--40 | The source provides Pauli-trajectory laws and reports stabilizer-QEC syndrome/logical statistics under the twirled model. | It gives no CAPEPS conditional state, reset transaction, raw syndrome-history mass ledger, frozen detector/observable fold, conditional fidelity, or Record total variation against an untwirled reference. | `missing` |
| matched CAPEPS/full-PEPS resources | complete source scope, represented by PDF pp. 18--20 and 40--41 | The source constructs SPP tensor-network representations and runs Pauli/HMM Monte Carlo studies. | It gives no matched quantum-state CAPEPS/full-PEPS benchmark, residual bond, measured runtime comparison, or peak host/device memory. | `missing` |

## Notation ledger

| symbol | source meaning | type/range | fixed or variable | exact source location |
|---|---|---|---|---|
| \(\Upsilon_{0:k}\) | Choi operator of a \(k\)-slot process tensor | positive operator on \(\bigotimes_{j=0}^k(\mathcal H_{i_j}\otimes\mathcal H_{o_j})\) with causal constraints | process-dependent | PDF pp. 9--10, Eqs. (9)--(16) |
| \(\mathcal T_P^{(k)}\) | multi-time Pauli-twirl superprocess | CPTP idempotent map on process Choi operators | fixed for \(n,k\) | PDF p. 15, Eq. (32) |
| \(\mathcal P=(P_0,\ldots,P_k)\) | spatiotemporal Pauli trajectory | element of \(\mathbb P^{(n,k)}\) | sampled | PDF p. 16, Eqs. (34)--(36) |
| \(w(\mathcal P),\Pr(\mathcal P)\) | unnormalized overlap weight and normalized Pauli-trajectory probability | nonnegative scalar and probability | trajectory-dependent | PDF p. 16, Eq. (35) |
| \(\mu_j\) | process/environment temporal virtual bond | Liouville-space index, dimension at most \(d_E^2\) for the finite-environment construction | time dependent | PDF pp. 12--13, Eqs. (20)--(24) |
| \(\nu_j^i\) | spatial tensor-network virtual bond | SVD/factorization bond, potentially truncated | site/time dependent | PDF pp. 14--15, Eqs. (29)--(30) |
| \(x_j\) | Pauli label emitted at time \(j\) | \(n\)-qubit Pauli label | sampled | PDF pp. 17--20, Eqs. (38)--(48) |
| \(A^x\) | local SPP MPS matrix | real/complex tensor whose contraction gives a nonnegative joint law; not automatically entrywise nonnegative in every gauge | model-dependent | PDF pp. 18--19, Eqs. (43)--(45) |
| \(T,E_f,\widetilde E_f\) | transfer, emission, and centered-emission operators | generally non-Hermitian matrices on the SPP bond space | model-dependent | PDF pp. 24--25, Eqs. (56)--(60) |
| \(D\) | SPP MPS/HMM latent bond dimension in Sec. 5 | positive integer | representation-dependent | PDF pp. 24 and 27--28, Eqs. (55), (69)--(75) |
| \(a,b\) | calm-to-storm and storm-to-calm transition probabilities | \([0,1]\), with \(a+b<1\) in the printed correlation-length formula | swept/fixed by experiment | PDF pp. 30--31, Eqs. (78)--(81) |
| \(\xi,\Delta\) | temporal correlation length and spectral gap of the two-state storm model | positive scalar and \(a+b\) | swept | PDF p. 30, Eq. (79) |
| \(d,N_r\) | rotated-surface-code distance and syndrome-extraction round count | selected positive integers; memory uses \(N_r=3d\) | workload-dependent | PDF pp. 31--32 and 39, Figs. 9 and 12 |
| \(s_t(i),x_t(i)\) | latent bath bit and emitted system Pauli at site \(i\), cycle \(t\) | \(\{0,1\}\) and \(\{I,X,Y,Z\}\) | sampled | PDF pp. 36--37, Sec. 7.2 |
| \(\theta\) | coherent controlled-rotation angle in the QCA bath | real angle | swept | PDF pp. 34--39, Eqs. (82), (85), (87) and Figs. 11--12 |
| \(\eta_t\) | instantaneous bath-excitation density | \([0,1]\) | trajectory-dependent | PDF p. 37, Eq. (94) |

## Operation reconstruction

`operation_replay_status = complete` for this audit means that the source's
load-bearing symbolic operations and the declared numerical workflow were
reconstructed and their replay limits recorded. It does not mean the Monte
Carlo curves were numerically reproduced from the PDF.

| input | transformation | assumptions | output | exact source location | replay verdict |
|---|---|---|---|---|---|
| process Choi operator \(\Upsilon_{0:k}\) | average independent Pauli conjugations on every time-pair | valid process tensor and fixed \(n,k\) | valid process-separable twirled Choi operator | PDF pp. 15--16, Eqs. (32)--(36); pp. 48--49, Appendix B | `symbolically_reconstructed` |
| process-tensor MPO/PEPO | contract fixed Pauli tensors into every open physical input/output pair | tensor network represents the source process; normalization retained | SPP MPS/PEPS of trajectory weights, Eqs. (43)--(48) | PDF pp. 18--20 | `symbolically_reconstructed`; no generic 2D contraction-cost claim |
| nonnegative row-stochastic SPP MPS gauge | identify \((K^x)_{ij}=(A^x)_{ij}\) | sufficient conditions in Eq. (74) | edge-emitting HMM with the same latent dimension | PDF pp. 27--28, Proposition 5.3 | `symbolically_reconstructed_under_sufficient_conditions` |
| two-state storm parameters and emissions | transition latent state, then emit a conditional Pauli | independent bath per system qubit and printed stationarity assumptions | fixed-marginal, tunable-correlation SPP/HMM | PDF pp. 29--31, Eqs. (76)--(81) | `symbolically_reconstructed` |
| storm/QCA SPP noise plus rotated surface-code circuits | sample Pauli faults, execute stabilizer circuits, decode with marginal MWPM | printed circuit/noise parameters, software families, and Monte Carlo shot counts | Figs. 9--12 logical-rate curves | PDF pp. 31--40 | `workflow_reconstructed__numerical_curves_not_independently_replayed`; no raw samples, seeds, environment lock, or pinned code commit in the PDF |
| classical bath state plus coherent QCA half-steps | system twirl induces bath dephasing; commute sublattice dephasing through the second half-step; apply Born weights of controlled rotations | assumptions (A1)--(A5), bipartite lattice, Hilbert--Schmidt-orthogonal conditional unitaries | two-stage PCA kernel \(\sin^2(k\theta)\) and conditional Pauli emission | PDF pp. 49--54, Eqs. (C1)--(C36) | `symbolically_reconstructed_under_printed_assumptions` |

## Printed and internal anomalies

These are source observations. They are not silently repaired in the reading
note, and none is transferred into project code.

1. **Choi-trace normalization.** PDF p. 10 prints
   \(\operatorname{Tr}\Upsilon_{0:k}=4^{n(k+1)}\). With the paper's own
   unnormalized Bell-state convention and Eq. (12), the \(k=0\) case instead
   recursively gives \(\operatorname{Tr}\Upsilon_{0:0}=\operatorname{Tr}I=2^n\).
   The printed exponent is therefore marked `SUSPECTED_AS_PRINTED`; this packet
   does not use it to normalize any project object.
2. **Missing adjoint in the main-text orthogonality line.** PDF p. 35, Eq. (90)
   prints \(\operatorname{Tr}(V_kV_l)=0\) for \(k\ne l\) while calling this the
   Hilbert--Schmidt inner product. Appendix C, Eq. (C6), prints the dimensionally
   standard \(\operatorname{Tr}(V_zV_{z'}^\dagger)=d_S\delta_{z,z'}\). The
   paper's specialized \(V_0=I,V_1=\vec n\cdot\vec\sigma\) are Hermitian, but
   the generic statements are not textually identical.
3. **Expanded Kraus terminology.** PDF p. 50, Eq. (C9) calls the double
   \(z,z'\) expansion a “general Kraus representation” even though it contains
   cross terms \(K_{P,z}\rho K_{P,z'}^\dagger\). It is equivalently obtained by
   first defining one aggregate Kraus operator per \(P\),
   \(K_P=\frac12\sum_z\Pi_z\otimes PV_zP\), and then expanding. The printed
   algebra is used only with this qualification.
4. **Reduced-system trace subscript.** PDF p. 53 defines
   \(\mathcal F[\rho_S]=\operatorname{Tr}_E(\widetilde{\mathcal U}^{SE}[\rho_E
   \otimes\rho_S])\) in Eq. (C29), but the first lines of Eq. (C30) visibly
   print \(\operatorname{Tr}_S\) before immediately reducing environment
   projectors to \(\operatorname{Tr}(\Pi_z\rho_E\Pi_{z'})\). The displayed
   subscript is marked `SUSPECTED_AS_PRINTED`; the surrounding operation is an
   environment trace.
5. **Cross-reference labels.** Appendix B says the twirl is defined in
   “Theorem 4.1,” although the source labels it Definition 4.1. Around
   Eqs. (39)--(46), the prose also refers to Theorems 4.5/4.6 where the displayed
   labels are Proposition 4.5 and Definition 4.6. These are reference-label
   defects, not new theorems.

## Source facts versus CAPEPS project application

The following statements are project inferences constrained by the source and
the repository contract; they are not Kam et al. claims.

- The comparator should be named an **operationally twirled SPP/tableau
  baseline** when it retains a joint correlated Pauli-trajectory law. Calling it
  merely “Pauli-twirled tableau” risks implying i.i.d. faults and discarding the
  very multi-time correlations this source preserves.
- Without the assumed frame-randomisation/randomised-compiling protocol, the
  SPP is a different effective process, not an exact representation of the
  original coherent channel. It may quantify a twirl-induced modeling change,
  but it cannot be advertised as a record-faithful approximation without a
  direct Record-law comparison.
- The SPP PEPS in Fig. 4 represents classical trajectory probabilities. It is
  not the CAPEPS residual \(\lvert\phi\rangle\), does not evolve conditional
  syndrome branches, and gives no CAPEPS disentangler.
- The current repository CAPEPS owner is an untruncated all-qubit
  engineering-mechanics prototype with raw `MeasurementEvent` branches and
  computational-basis measure-reset. This source neither validates nor
  contradicts that algebra; it supplies no canonical `RecordBatch` bridge,
  finite-bond error bound, or resource result.
- A future comparison must freeze whether it compares the original coherent
  circuit, the physically randomized circuit, or a post-hoc twirled model.
  Those are distinct estimands.

## Admission boundary

This packet remains a draft until an independent reviewer rereads the exact
PDF and checks the note/audit pair. No `CURRENT_CORPUS.toml` entry is authorized
by this audit alone. Even after source-only admission, the source can support
only the bounded SPP/twirled-baseline facts above; it cannot authorize a CAPEPS
target experiment, a Record-law claim, or an efficiency conclusion.
