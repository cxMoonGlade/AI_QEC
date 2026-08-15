# Project-fit audit — Rudolph and Tindall, arXiv:2507.11424v2

Date: 2026-07-17

## Frozen question

Does the terminal planar-TNS sampling method of Rudolph and Tindall provide a finite-truncation
accuracy bridge for an adaptive, multi-round QEC detector `Record` law?

The source object is `outputs/papers/pepo_survey/2507.11424.pdf`, SHA-256
`780b8fad4917a9a2031aff235a699999f47b95602922d6ddf912ef946912ce00`, identified by
the PDF metadata and stamp as arXiv:2507.11424v2. The complete 13-page object was read.
Load-bearing pages 1, 3, 4, 5, 7, 8, 9, 11, 12, and 13 were rendered and visually checked.

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| finite-PEPS gate truncation | Sec. II, Eqs. (1)-(2), p. 3; App. Eq. (10), p. 13 | BP-conditioned simple update truncates each two-site gate to bond dimension `chi`; the discarded-weight fidelity relations are approximate on loopy networks and exact only without truncation for the represented state. | It does not turn local discarded weight into an exact global distribution bound. | closed |
| terminal sampling law | Sec. II, pp. 4-5; App. Fig. 7, pp. 11-12 | The method samples one final computational-basis bitstring `x` from `q(x)` after the circuit; `p(x)=|<x|psi>|^2` is the distribution encoded by the final TNS. | It does not sample intermediate measurements, resets, or adaptive conditional circuit branches. | closed |
| sampled-law diagnostic | Eq. (5), p. 4 | For `x~q`, the mean importance ratio `p(x)/q(x)` equals the norm of the represented TNS. | That identity is not a total-variation or worst-event bound. | closed |
| distribution discrepancy | Eq. (6), p. 4 | The paper evaluates `KLD(q,p)=E_q[log(q/p)]` for the terminal bitstring distributions. | It does not derive detector-Record TV or LER error from this KLD. | closed |
| independent terminal probability evaluation | Sec. II, p. 4; App. Fig. 7 and text, p. 11 | Each sampled terminal probability can be recomputed by a separate boundary-MPS contraction of `<x|psi>`. | The verifier still targets the same final TNS, not an independent physical circuit or adaptive Record oracle. | closed |
| topology-dependent convergence | Figs. 3-6, pp. 7-8 | Heavy-hex and Willow require very different boundary-MPS dimensions; at Willow depth 15, local observables require about `R=75` although `chi=20`. | No geometry-independent finite `R` certificate is given. | closed |
| local observable versus global distribution | Fig. 4, p. 7 | At sample KLD around 2, the tested local expectation values can be accurate while the full terminal distribution remains different. | Local-observable convergence does not certify the full terminal law. | contradicted |
| adaptive multi-round Record law | Complete method/results scope, especially pp. 2-8 and App. pp. 11-13 | The source addresses unitary pure-state circuits followed by final-basis sampling. | It gives no repeated measurement/reset transition kernel, detector XOR folding, logical-observable bit, temporal ordering, or full Record distribution. | missing |
| terminal KLD to Record TV/LER bridge | Eqs. (5)-(6), p. 4; conclusion, pp. 8-9 | The source reports terminal `p/q`, KLD, symmetry-sector rates, and selected observables. | It gives no theorem or experiment relating those quantities to adaptive multi-round Record TV or logical-error-rate deviation. | missing |

## Notation ledger

| symbol | source meaning | domain or status | locator |
|---|---|---|---|
| `|psi_i>` | approximate pure TNS after gate `i` | planar graph matched to the circuit geometry | Sec. II, pp. 2-3 |
| `chi` | maximum state-TNS virtual bond dimension | gate-truncation control | Eq. (1), p. 3 |
| `epsilon_i` | sum of discarded squared singular values for gate `i` | approximate gate infidelity on loops | Eq. (1), p. 3 |
| `f` | product of `1-epsilon_i` over gates | approximate final-state fidelity | Eq. (2), p. 3 |
| `R_n` | boundary-MPS dimension for reverse contraction of `<psi|psi>` | norm-network contraction control | Sec. II, p. 4; Fig. 7, p. 11 |
| `R_x` | boundary-MPS dimension for forward contraction while sampling `<x|psi>` | sampling contraction control | Sec. II, p. 4; Fig. 7, p. 11 |
| `q(x)` | distribution actually sampled at finite `R_n,R_x` | product of sequential conditional probabilities within the terminal bitstring sampler | pp. 4 and 11 |
| `p(x)` | `|<x|psi>|^2` encoded by the final TNS | terminal computational-basis weight | pp. 4 and 11 |
| `KLD(q,p)` | `E_q[log(q/p)]` | terminal-distribution discrepancy used by the paper | Eq. (6), p. 4 |
| `epsilon_l` | primitive-loop transfer-matrix separability error | first-order BP error diagnostic | Eqs. (3)-(4), p. 3 |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Initial product state and unitary circuit | Apply one-site gates exactly and two-site gates through BP-conditioned simple update. | Pure-state qubit circuit; planar graph; message approximation for loops. | Final planar TNS `|psi>` with bond cap `chi`. | Sec. II, pp. 2-3; App. Eq. (10), p. 13 | checked |
| Two-site update | SVD the gauged local region and discard singular values beyond `chi`. | Eq. (1) is an approximate fidelity relation on loopy graphs. | Local discarded weight `epsilon_i` and updated TNS. | Eq. (1), p. 3; App. Fig. 8 and Eq. (10), pp. 12-13 | checked |
| Final TNS | Partition the norm network and run reverse MPS-MPO fits at dimension `R_n`. | The chosen partitions form a line. | Cached right environments for all terminal samples. | Sec. II, p. 4; App. Fig. 7, p. 11 | checked |
| Cached norm environments | Move left to right, sample site projectors conditionally, and fit sampled partitions at dimension `R_x`. | This samples the final computational basis only. | One terminal bitstring `x` and its sampler probability `q(x)`. | App. Fig. 7 and text, pp. 11-12 | checked |
| Terminal bitstring | Contract `<x|psi>` separately or with sufficiently large `R_x`. | This verifies probability in the represented TNS. | `p(x)=|<x|psi>|^2`. | Sec. II, p. 4; App. p. 11 | checked |
| Samples and paired probabilities | Average `p/q` and `log(q/p)`. | All sampled support ratios used in importance weighting must be finite. | Norm estimator, KLD, and optional importance-weighted observable. | Eqs. (5)-(6), p. 4; Eq. (9), p. 12 | checked |
| Increased `R` | Repeat contractions and sampling. | Convergence is empirical for the studied circuits; pathological PEPS can require exponential `R`. | Terminal-law and observable convergence plots. | Figs. 2-6, pp. 5-8; conclusion, p. 9 | checked |

The replay stops after one terminal bitstring. There is no source step that updates a state after a
measurement, applies a per-target reset, branches a later operation on an earlier outcome, folds raw
syndromes into temporal detectors, or appends a logical-observable bit.

## Why terminal `p/q` and KLD are not the adaptive multi-round Record metric

The mismatch is structural, not merely terminological:

1. The paper's sample `x` is one final computational-basis string from one final pure TNS.
2. A multi-round QEC `Record` is an ordered joint law over outcomes generated by repeated
   measurement, conditional state updates, possible resets, and later dynamics.
3. The detector coordinate is additionally a deterministic temporal XOR transform of raw syndrome
   outcomes and may include logical-observable flips.
4. Eq. (5) is an expectation identity for importance ratios; it is not a uniform bound on event
   probabilities.
5. Eq. (6) is a KL discrepancy for the terminal `q` and `p` selected by the paper. The paper gives no
   bridge from it to the joint adaptive Record distribution, no total-variation acceptance band, and
   no logical-error-rate consequence.
6. Figure 4 itself shows that selected local observables can converge while the full terminal
   distribution remains different. This blocks promotion from local accuracy to global-law accuracy
   even before the additional multi-round structure is introduced.

This reasoning is a project inference from the source boundary and `docs/SIMULATOR.md`; it is not a
claim made by Rudolph and Tindall and therefore remains outside the source-only reading note.

## Project application

The source is useful for a terminal PEPS sampling subroutine and for designing diagnostics:

- distinguish the state-TNS bond cap `chi` from boundary contraction dimensions `R_n,R_x`;
- return the actual sampler probability `q(x)` and, where feasible, independently contract `p(x)` for
  the represented TNS;
- sweep `R` because topology can make the required contraction dimension far larger than `chi`;
- preserve approximate gate-discarded weight, BP loop error, terminal KLD, symmetry-sector rate, and
  local-observable convergence as separate diagnostics;
- do not use GPU speed or terminal normalization as a scientific certificate.

For the current single-wire PEPS research carrier, the paper can motivate terminal-sampling
mechanics. It cannot establish complete multi-round finite-truncation faithfulness. A project
extension would need an explicitly defined sequence-law sampler, schedule-sealed Record layout,
independent dense or exact Record oracle in a feasible regime, total-variation comparison on aligned
support, and record-order/fold corruptions.

## Competing evidence and kill conditions

The paper explicitly preserves two disconfirming facts: Eq. (1) and Eq. (2) are approximate on
loopy networks, and finite-dimensional pathological TNS can require `R` exponential in system size
for perfect sampling. It also reports topology-sensitive convergence rather than a universal `R`.

The following uses are killed by the source boundary:

- treating local discarded singular weight as an exact final-law error;
- treating `p/q` mean near one as a worst-event or TV bound;
- treating accurate local observables as proof of a globally accurate distribution;
- equating one terminal bitstring distribution with an adaptive multi-round detector Record;
- transferring the reported heavy-hex/Willow dimensions or 32-bit GPU timings into a general
  precision or resource gate;
- calling the separate `<x|psi>` contraction an independent oracle for the physical circuit rather
  than a verification of the represented final TNS.

## Source-local verdict

- `read_status: complete`
- `evidence_status: persisted`
- terminal planar-TNS sampling mechanism: `closed`
- terminal `p/q` and KLD definitions: `closed`
- topology-independent finite-`R` guarantee: `missing`
- adaptive multi-round Record law: `missing`
- terminal-metric-to-Record-TV/LER bridge: `missing`
- allowed downstream use: terminal PEPS sampling mechanics and diagnostic design
- prohibited downstream use: complete Record-law, TV, LER, or canonical-backend certification
