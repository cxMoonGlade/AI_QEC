# Claim audit — Schuch et al. PEPS complexity and project relevance

## Status and decision

Retain Schuch, Wolf, Verstraete, and Cirac, *Computational Complexity of
Projected Entangled Pair States*, as the complexity boundary for exact
computation of PEPS norm, unnormalized expectation value, and normalized
expectation value, and for exact general tensor-network contraction.

The source establishes a worst-case problem-class result. It does **not**
establish that every physical PEPS, every approximation regime, or this
repository's finite XZZX distance-7 instance is hard. It therefore limits any
claim of a generally exact polynomial PEPS solver, but it neither rejects nor
certifies a structured finite-size PEPS/PEPO carrier. Under the standard
`FP != #P` assumption, it blocks an unrestricted exact polynomial solver that
covers arbitrary instances of the paper-defined PEPS primitives; a combined
PEPS/PEPO engine inherits that barrier only through arbitrary-PEPS coverage.

## Source and review boundary

- Version of record: Physical Review Letters 98, 140506 (published 4 April
  2007), DOI `10.1103/PhysRevLett.98.140506`.
- Reviewed artifact:
  `docs/papers/schuch_wolf_verstraete_cirac_prl_98_140506.pdf`.
- Artifact SHA-256:
  `e996af2b5d573e3befd249f69fdfd29284c2a656134a80f46d9351eb9da51537`.
- Full text read: all four pages.
- Visually checked: PDF pp. 1--4, including the path-pair expression and
  reductions on pp. 3--4.
- The expanded arXiv v2 was used only to cross-check source discovery. The
  admitted claims below are located in the version-of-record artifact.

## Assigned closure rows

| row | exact source location | source says | source does not say | status |
|---|---|---|---|---|
| PEPS definition | “PEPS and postselection,” PDF p. 1, right column | A PEPS is defined on an arbitrary undirected graph by maximally entangled virtual pairs of dimension `D` and local linear maps into physical dimension `d`. | This definition is not a contraction algorithm or an efficiency guarantee. | closed |
| Postselected circuit to PEPS | “PEPS and postselection,” PDF pp. 1--2 | A postselected circuit is encoded efficiently through cluster-state measurement-based computation as a square-lattice PEPS with `D=d=2` and size polynomial in circuit length. | It does not give a practical low-bond simulation guarantee for generic circuit outputs. | closed |
| PEPS to postselection | “PEPS and postselection,” PDF p. 2, left column | The source implements each local linear map as a postselected POVM element and states an efficient transform from PEPS to a postselected circuit. | This is a state-preparation equivalence, not a classical contraction method. The version of record does not spell out the graph-degree or tensor-description-size condition under which the reverse transform is efficient. | closed with source-local input-encoding ambiguity |
| Simulation primitives | “The classical complexity of PEPS,” PDF p. 2, right column; note [16], PDF p. 4 | The problems are PEPS norm, unnormalized expectation value, and normalized expectation value, with weakly parsimonious reductions between them. | These primitives are not a sampled trajectory or a joint multi-round measurement Record. | closed |
| PEPS hardness | “The classical complexity of PEPS,” PDF p. 2, final paragraph | Encoding the circuit that prepares `sum_x |x>|f(x)>` as a PEPS makes a normalized `sigma_z` expectation determine the satisfying-assignment count. | It is not an average-case or instance-specific lower bound. | closed |
| PEPS membership and completeness | “The classical complexity of PEPS,” PDF pp. 2--3; note [16], PDF p. 4 | A Toffoli/Hadamard path-pair sum reduces the norm to a Boolean count, yielding membership in `#P`; together with hardness, the paper-defined exact PEPS primitives are `#P`-complete under weakly parsimonious reductions. | It does not assign a finite runtime or required bond dimension to a named physical instance. The version of record does not expand how generic tensor coefficients or gate-synthesis precision preserve the exact quantity after it says to approximate the postselected circuit by Toffoli and Hadamard gates. | closed with source-local encoding/precision ambiguity |
| General tensor-network contraction | “The classical complexity of PEPS,” PDF p. 3, left column | PEPS gives hardness; `T tensor T*`, a physical dimension-one system at each site, PEPS norm queries, and tensor direct sums are used to state that general tensor-network contraction is `#P`-complete. | The short reconstruction explicitly recovers `abs(Re C(T))` and its sign, but it does not separately expand imaginary-part recovery or a coefficient-encoding convention. | closed with source-local ambiguity |
| Approximation statement | “The classical complexity of PEPS,” PDF p. 3, left column | Linear postprocessing transfers the reductions to the corresponding approximate-counting difficulty. | No additive/multiplicative error model, precision scaling, success probability, promise, or FPRAS theorem is specified. | closed as qualitative scope only |
| Physical-instance scope | “The power of creating ground states,” PDF p. 3, right column | In its ground-state-oracle discussion, the source calls the PEPS that encapsulate PP problems “quite artificial.” | It does not classify finite open-boundary, low-depth, weak-noise, XZZX, leakage, or distance-7 instances. | missing |
| Project Record bridge | Full-text scope, PDF pp. 1--4 | The source treats state preparation and scalar contraction/expectation primitives. | It gives no PEPO dynamics, selective measurement/reset rule, branch-mass reconciliation, detector folding, logical-observable law, Record TV, or LER certification. | missing |

## Notation ledger

| symbol | source meaning | project-use restriction |
|---|---|---|
| `d` | local physical Hilbert-space dimension | Do not identify the paper's illustrative `d=2` hardness construction with this project's qutrit leakage dimension. |
| `D` | PEPS virtual-bond dimension | Do not confuse it with code distance or an environment/contraction bond. |
| `P^[v]` | local map from incident virtual spaces to the physical space | This is a PEPS tensor map, not a syndrome projector or project adapter. |
| `NORM` | PEPS normalization | A scalar primitive, not the normalization of every stochastic branch in a Record generator. |
| `UEV` | unnormalized expectation value | A scalar primitive. |
| `NEV` | normalized expectation value | A scalar primitive. |
| `C(T)` | scalar contraction of a general tensor network `T` | The source's general contraction problem is broader than this repository's structured networks. |
| `#P` | exact counting complexity class used by the reductions | A worst-case asymptotic class, not a measured resource estimate. |

## Operation replay

### Exact PEPS hardness

1. Start from a polynomial Boolean function `f`.
2. Build a quantum circuit whose output is proportional to
   `sum_x |x>_A |f(x)>_B`.
3. Encode that circuit output as a PEPS using the postselection-to-PEPS
   construction.
4. Evaluate the normalized expectation of `sigma_z` on register `B`.
5. Recover the satisfying-assignment count `s(f)` by linear
   postprocessing.

This closes the source's `#P`-hardness direction for the exact PEPS
simulation primitive.

### Membership in `#P`

1. Translate the PEPS into a postselected circuit and approximate that circuit
   with Toffoli and Hadamard gates.
2. Expand an output probability as a sum over pairs of computational paths.
3. Express the postselection-success norm as a sum of an efficiently
   computable function taking values in `{0, +1, -1}`.
4. Reduce that signed sum to satisfying-assignment counts plus linear
   postprocessing.

This is the source's membership argument; combined with the first replay, it
gives the stated `#P`-complete result under weakly parsimonious reductions.
The audit does not fill the source-local encoding/precision bridge between
approximating a generic postselected circuit by this gate set and preserving
the exact quantity for arbitrary tensor coefficients.

### General tensor-network contraction

1. Use PEPS contraction as the hard special case.
2. Form `T tensor T*`, attach a physical dimension-one system at every site,
   and query the norm of the resulting PEPS to obtain `|C(T)|^2`.
3. Use tensor direct sums to turn contraction into scalar addition and recover
   the real component and its sign.
4. State membership and completeness for the general contraction problem.

The version of record states the conclusion, but its compact recovery
paragraph explicitly obtains only `abs(Re C(T))` and its sign; it does not
separately expand imaginary-part recovery or a coefficient-encoding
convention. No stronger reconstruction theorem is inferred here.

### Approximation transfer

The source observes that the exact reductions need only linear
postprocessing, so an approximation to a PEPS primitive induces an
approximation to the corresponding counting quantity. Because it does not
fix an error convention, this replay supports only the source's qualitative
“as hard as approximating counting problems can be” statement.

## Project application

- Under the standard `FP != #P` assumption, the result blocks an unrestricted
  exact polynomial solver covering arbitrary PEPS norm and expectation-value
  instances. A combined PEPS/PEPO engine inherits this barrier only insofar as
  it covers arbitrary PEPS instances; the paper does not prove hardness for a
  separately restricted PEPO class.
- It does not kill an empirical finite-size carrier for the project's fixed
  geometry and noise family. Such a carrier must instead expose independent
  state bond and environment/contraction controls, then be tested against
  dense or otherwise independent references.
- It does not turn local truncation residuals or converged scalar observables
  into a full multi-round Record guarantee.
- It supplies no basis for choosing PEPS over PEPO, no PEPO positivity
  result, and no estimate for distance-7 XZZX non-Pauli leakage.

## Competing evidence and kill conditions

- Structured or restricted PEPS families can remain tractable without
  contradicting this worst-case result; any such claim needs its own
  assumptions and source.
- Numerical success at one bond dimension does not refute the theorem, and
  the theorem does not invalidate numerical success on one instance.
- Kill any downstream sentence that changes “exact worst-case PEPS
  simulation is `#P`-complete” into “all PEPS approximations are
  `#P`-complete.”
- Kill any downstream resource forecast for XZZX distance 7 that cites this
  paper without an instance-specific scaling study.
- Kill any use of `NORM`, `UEV`, or `NEV` as if the paper had defined the
  repository's detector/observable Record.

## Source-local verdict

- `read_status`: complete
- `evidence_status`: persisted
- exact simulation rows: closed
- quantitative approximation row: missing
- PEPO/QEC/Record rows: missing
- project fit: general exact-complexity boundary only
