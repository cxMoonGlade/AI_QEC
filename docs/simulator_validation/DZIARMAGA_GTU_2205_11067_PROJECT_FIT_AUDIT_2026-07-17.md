# Project-fit audit — Dziarmaga GTU 2205.11067v3

Date: 2026-07-17
Source artifact: `outputs/papers/pepo_survey/2205.11067.pdf`
Source SHA-256: `f4f15976158cf506b476c9eb17c4390e3fa186934a54aad8d3727ee49e05af7f`
Question: what does gradient tensor update establish about environment-aware PEPS truncation, and
does its tangent-space or overlap objective certify a trajectory, detector Record, or logical statistic?

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| Exact-to-truncated iPEPS operation | Sec. II, Fig. 1, PDF pp. 1–2 | A nearest-neighbor Trotter gate increases one iPEPS bond from `D` to `rD`; GTU seeks new `D`-bond tensors maximizing overlap with that enlarged-bond pure state. | It does not treat a finite PEPS boundary, mixed density operator, stochastic trajectory, or measurement branch. | closed |
| Tangent-space step | Sec. II, Eqs. (1)–(7), PDF p. 2 | Orthogonal state variations define a quadratic cost with a Gram–Schmidt metric and gradient; a pseudoinverse direction is followed by a line search maximizing overlap per site. | The source does not prove global convergence of the alternating nonlinear optimization. | closed |
| Environment metric | Sec. III, Eqs. (10)–(12), PDF p. 3 | The metric is a sum of connected derivative correlations and is evaluated by CTMRG like a connected correlation function, with nonzero contributions within the correlation range. | No error bound is given for the approximate CTMRG contraction, finite environment dimension, or metric pseudoinverse. | closed at mechanism level |
| Truncation objective | Sec. II, Eqs. (7)–(9), PDF pp. 2–3 | Each SVDU, NTU, and GTU stage is evaluated by an overlap per lattice site between the enlarged- and reduced-bond infinite pure-state iPEPS. | `1-O` is not proved to equal a finite-system state norm, trace distance, trajectory-law distance, or observable bound. | closed with limited semantics |
| Reduced-tensor implementation | Appendix A, Fig. 6, PDF p. 7 | Fixed QR isometries reduce the optimized parameter and metric dimensions from `D^4 d` to `D^2 d` before rebuilding the full tensors. | This reduction does not supply a truncation or contraction error theorem. | closed |
| Empirical improvement | Sec. IV, Fig. 4; Appendix B, Figs. 7–8, PDF pp. 4, 7–9 | On the two declared Ising quenches, GTU extends reachable evolution and reduces `1-O` beyond NTU/SVDU; runs stop on an energy-drift or overlap threshold. | These benchmarks do not prove model-independent superiority, monotone nondegeneracy, or an observable certificate. | closed as benchmark only |
| Detector Record bridge | Full-text scope: abstract; Secs. I–VI and appendices, PDF pp. 1–9 | The source evolves an infinite pure-state iPEPS unitarily and reports magnetization, energy drift, excitation energy, and overlap per site. | It defines no stochastic branch mass, repeated measurement law, detector event, logical bit, Record distance, or logical-error-rate bound. | missing |

## Notation ledger

| source symbol | source meaning | domain or scope | fixed/variable |
|---|---|---|---|
| `D` | retained iPEPS bond dimension | infinite checkerboard pure-state ansatz | user-controlled |
| `rD` | bond dimension after a rank-`r` Trotter gate | one updated nearest-neighbor bond family | gate-dependent |
| `phi` | exact enlarged-bond iPEPS after the gate | one Trotter update | source target |
| `psi` | reduced-`D` variational iPEPS | alternating `A''`, `B''` optimization | candidate |
| `G_{mu nu}` | Gram–Schmidt tangent-space metric | variations of one reduced tensor family | state/environment-dependent |
| `J_mu` | overlap-derived tangent-space gradient | same parameter space as `G` | state/target-dependent |
| `O` | overlap per lattice site | thermodynamic-limit iPEPS comparison | stage diagnostic |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| checkerboard iPEPS and nearest-neighbor Trotter gate | apply the rank-`r` gate on equivalent bonds | unitary evolution split into nearest-neighbor gates | enlarged-bond target `phi` with bond `rD` | Secs. I–II and Fig. 1, PDF pp. 1–2 | reproduced |
| reduced-bond candidate `psi` | project tensor variations orthogonal to `psi` and construct quadratic cost | linearized tangent-space neighborhood | metric `G`, gradient `J`, and pseudoinverse direction | Eqs. (1)–(5), PDF p. 2 | reproduced |
| pseudoinverse direction | line search over real `x` | near the current tangent point; overlap contractions available | accepted tensor update maximizing `O_x` along that line | Eqs. (6)–(7), PDF p. 2 | reproduced |
| gate-enlarged tensors | SVDU, then NTU, then alternating GTU | NTU initialization is used to reduce local-minimum risk | reduced-bond iPEPS and `O` after every stage | Eqs. (8)–(9), PDF p. 3 | reproduced |
| derivative insertions across sublattice | subtract disconnected component and sum correlations | translation-invariant infinite checkerboard; finite represented correlation range | CTMRG estimate of metric and gradient | Eqs. (10)–(12), PDF p. 3 | reproduced at declared numerical-method level |
| per-site overlap `O` | reinterpret as finite-state trace distance or historical Record distance | no such theorem is supplied | no source-supported output | full-text boundary, PDF pp. 1–9 | blocked |

## Project application

GTU is directly relevant to the project's PEPS truncation frontier as an example of an
environment-aware objective that goes beyond one-bond SVD or a fixed local cluster. It supports three
narrow design lessons:

1. The source and candidate tensors must remain distinct during optimization; success is judged against
   the enlarged-bond target, not by a self-comparison of the already truncated candidate.
2. Environment sensitivity enters through connected derivative correlations and the tangent-space metric;
   an accepted update therefore needs authenticated environment/metric inputs and a no-op failure path when
   these inputs are invalid.
3. Cheap-to-expensive staging (`SVDU -> NTU -> GTU`) and explicit before/after objective values are valid
   engineering precedents, but they do not create a scientific nondegeneracy or Record certificate.

The following bridges remain unsupported:

- finite iPEPS or PEPS geometry from the thermodynamic checkerboard derivation;
- pure-state unitary GTU to mixed PEPO or quantum-trajectory truncation;
- finite CTMRG environment dimension to an exact global environment;
- overlap per site or energy drift to global state fidelity, trace distance, branch mass, detector Record
  total variation, or logical-error-rate error;
- a successful line search to guaranteed rank reduction or to an always-improving physical observable.

The paper therefore motivates a better truncation objective and a corruption surface, but cannot close the
current PEPS FET nondegeneracy or full-record bridge.

## Competing evidence and kill conditions

- Lubasch et al. 1405.3259 treats finite PEPS environments and explicitly records that approximate
  environments can lose exact positivity and that finite PEPS lacks the simple open-boundary MPS
  canonical identity; that limits direct transfer of this infinite-iPEPS metric.
- Werner et al. 1412.5746v2 gives a trace-norm certificate only for a one-dimensional locally purified
  density operator with canonical compression; GTU's `1-O` is not that discarded weight.
- Kill a claim that calls CTMRG “the exact global environment,” because the source gives no finite-CTMRG
  contraction-error bound.
- Kill a state- or Record-faithfulness claim that substitutes `1-O`, energy drift, magnetization agreement,
  accepted update count, or a rank reduction for an independent full observable comparison.
- Kill a mixed-state/PEPO implementation claim that cites this source without a new derivation of the
  objective, metric, positivity, and compression semantics.

## Source-local verdict

- read_status: complete
- evidence_status: persisted
- tangent-space/environment mechanism row: closed
- overlap-objective row: closed with limited per-site semantics
- contraction/error-certificate row: missing
- trajectory and detector Record row: missing
- project disposition: `supports_environment_aware_PEPS_truncation_design_only`
- current gate effect: PEPS scientific nondegeneracy remains RED; full-record bridge remains open
