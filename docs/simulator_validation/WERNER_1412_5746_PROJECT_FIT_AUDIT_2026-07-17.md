# Project-fit audit — Werner et al. 1412.5746v2

Date: 2026-07-17
Source artifact: `docs/papers/werner_positive_tensor_network_open_systems_1412.5746.pdf`
Source SHA-256: `a5930d27f28e322d4216384c9ff28e8db7a865fa951a6b33ad5a621fa66a2f2f`
Question: what positivity and trace-norm guarantees follow from locally purified tensor evolution,
and can they be transferred to two-dimensional, trajectory, or historical detector-Record claims?

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| Structural positivity | Main text, Eq. (3) and Fig. 1, PDF pp. 1–2 | Representing the finite-chain density operator as `rho = X X^dagger` and evolving/compressing `X` keeps every represented density operator positive. | Positivity alone does not establish trace preservation, small error, or correctness of historical measurement statistics. | closed |
| Local Markovian update | Main text, Eqs. (1)–(6), PDF pp. 1–2 | Second-order Trotter layers act coherently on `X`; completely positive on-site channels enlarge the local Kraus dimension and are then compressed. | The main formula does not cover non-Markovian memory or arbitrary long-range Liouvillians. | closed |
| Nearest-neighbor channels | Main text Eq. (10); Appendix C.1, Eqs. (45)–(54), PDF pp. 4, 9–10 | A nearest-neighbor Liouvillian channel is exponentiated, Choi transformed, Kraus decomposed, and split across two local tensors with a gauge-dependent preprocessing. | The Kraus split optimization is nonlinear and is not proved globally optimal or efficient. | closed |
| Purification-to-state norm bridge | Appendix A, Lemma 1, Eqs. (20)–(25), PDF p. 6 | For normalized density operators represented as purifications, purification 2-norm distance bounds density trace norm and fidelity. | It does not identify an arbitrary tensor objective with purification 2-norm distance. | closed |
| Canonical SVD compression | Appendix D, Definition 5 and Lemma 6, Eqs. (55)–(58), PDF pp. 10–11 | At a mixed-canonical local tensor, omitted singular values define a purification-space discarded weight and determine the normalized purification 2-norm error. | This statement does not apply to a noncanonical PEPS environment fidelity or a stochastic branch-probability loss. | closed |
| Trace-norm certificate | Appendix D, Theorem 7, Eqs. (59)–(73), PDF pp. 11–12 | For a finite one-dimensional nearest-neighbor Liouvillian with bounded local diamond norms, second-order Trotter evolution and uniformly bounded canonical discarded weights give the stated final-state trace-norm upper bound. | The theorem gives no a priori efficient bound on discarded weight and no theorem for 2D PEPO, quantum trajectories, or a historical Record discarded during evolution. | closed under explicit hypotheses |
| Two-dimensional extension | Appendix E and Fig. 7, PDF pp. 12–13 | The ansatz and local-channel layers can be drawn in 2D, but exact contraction is worst-case hard; bond compression is only expected to generalize, and Kraus-dimension compression is described as less obvious. | No 2D algorithm, canonical form, benchmark, or trace-norm theorem is established. | missing for certification |
| Detector Record bridge | Full-text scope: main text and appendices, PDF pp. 1–13 | The certified output is a final finite-chain density operator and its expectation values. | The source defines no repeated detector measurement register, temporal XOR law, trajectory branch law, full Record total variation, or logical-error-rate theorem. | missing |

## Notation ledger

| source symbol | source meaning | domain or scope | fixed/variable |
|---|---|---|---|
| `rho = X X^dagger` | locally purified density operator | finite one-dimensional open chain | time-dependent |
| `D` | bond dimension of purification operator `X` | local MPS-like links | truncation-controlled |
| `K` | local Kraus dimension of `X` | local purification index | channel- and truncation-controlled |
| `k` | Kraus rank of an applied local channel | at most `d^2` on-site or `d^4` two-site | channel-dependent |
| `delta` | square root of the sum of squared discarded singular values | one mixed-canonical bond or Kraus compression | runtime diagnostic |
| `b` | uniform diamond-norm bound on each nearest-neighbor Liouvillian term | Theorem 7 | assumed finite bound |
| `m` | number of second-order Trotter time steps | Theorem 7 | user-controlled |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| locally purified initial state | apply coherent TEBD layers to `X` and local CP channels through Kraus operators | finite open chain; local Markovian Liouvillian; Trotter layering | enlarged-bond/Kraus purification still representing a positive state | Eqs. (1)–(6), Fig. 1, PDF pp. 1–2 | reproduced |
| enlarged local tensor | mixed-canonical SVD on one bond or Kraus index, discard tail, renormalize | `X` is canonical at the compressed tensor and normalized | compressed purification with Eq. (56) 2-norm error | Definition 5 and Lemma 6, Eqs. (55)–(58), PDF pp. 10–11 | reproduced |
| two normalized purifications | apply Lemma 1 | both products are density operators | state trace-norm and fidelity bounds | Eqs. (20)–(25), PDF p. 6 | reproduced |
| finite nearest-neighbor chain | split even/odd Liouvillian, apply `2m+1` channel layers, compress all three virtual indices per site | local diamond norms bounded by `b`; every discarded weight bounded by the declared maximum | final-state trace-norm bound combining Trotter and compression terms | Theorem 7 and Eqs. (59)–(73), PDF pp. 11–12 | reproduced under hypotheses |
| two-dimensional positive PEPO sketch | apply the one-dimensional theorem unchanged | no exact 2D canonical representation or compression theorem is supplied | no source-supported 2D certificate | Appendix E, PDF pp. 12–13 | blocked |
| final density-state trace norm | infer an already discarded multi-time measurement history | historical register is absent from the certified state | no source-supported Record bound | full-text boundary, PDF pp. 1–13 | blocked |

## Project application

Werner et al. provides the strongest rigorous truncation certificate in this reading set, but only for a
different carrier class from the current restricted MPS trajectories and PEPS frontier. The valid project
mapping is narrow:

- A future finite one-dimensional locally purified density carrier can preserve positivity structurally and
  can ledger Trotter error separately from canonical purification-compression error.
- The certificate's `delta` is a specific SVD tail at a mixed-canonical tensor, followed by the paper's
  renormalization. It is not an arbitrary local discarded fraction, CTMRG overlap, FET environment
  fidelity, or physical no-jump norm loss.
- The trace-norm bound controls the final density state and therefore final-time expectation values under
  the theorem's assumptions. It does not retroactively reconstruct a measurement history that the state no
  longer contains.

A bound on a complete classical measurement Record would require explicitly retaining that Record in the
certified output state/channel and then supplying a new project derivation using trace-distance
contractivity. The source neither builds that augmented register nor proves its local Liouvillian and
compression hypotheses after repeated measurement/reset. That possible bridge is therefore project
inference, not a paper fact.

The 2D positive-PEPO figure is a research prospect. The text itself warns that canonical compression is
needed, exact contraction is worst-case hard, and Kraus-dimension compression is less obvious. Theorem 7
must not be transferred to the current PEPO/PEPS carriers without a new 2D canonical/error derivation.

## Competing evidence and kill conditions

- Dziarmaga GTU 2205.11067v3 supplies an environment-aware pure-iPEPS overlap objective, but its `1-O`
  is not Werner's mixed-canonical purification discarded weight and has no analogous trace-norm theorem.
- Lubasch et al. 1405.3259 documents why finite PEPS lacks the simple MPS canonical identity and why
  approximate environments can violate exact positivity, blocking a casual 1D-to-2D transfer.
- Kill a trace-norm claim if the execution is a stochastic trajectory rather than the locally purified
  density carrier defined in Eq. (3).
- Kill the certificate if the local Liouvillian support, diamond-norm bound, second-order layering,
  normalization, mixed-canonical compression, or complete discarded-weight ledger is missing.
- Kill any 2D/PEPO theorem claim based only on Appendix E or Fig. 7.
- Kill a detector Record or logical-error-rate claim if the complete classical record register was not part
  of the certified state throughout the evolution.

## Source-local verdict

- read_status: complete
- evidence_status: persisted
- structural positivity row: closed
- one-dimensional final-state trace-norm row: closed under Theorem 7 hypotheses
- two-dimensional certificate row: missing
- trajectory and detector Record row: missing
- project disposition: `rigorous_for_future_1D_locally_purified_density_carrier_only`
- current gate effect: no upgrade to restricted MPS, PEPO, PEPS, or full-record acceptance
