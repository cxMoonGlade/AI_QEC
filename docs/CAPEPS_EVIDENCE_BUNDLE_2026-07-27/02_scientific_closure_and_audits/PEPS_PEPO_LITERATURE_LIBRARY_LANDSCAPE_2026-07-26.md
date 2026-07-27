# PEPS/PEPO literature and library landscape — 2026-07-26

## Decision

No inspected library directly implements the complete target:

> finite two-dimensional XZZX distance 7, local qutrit leakage, non-Pauli
> stochastic channels, repeated selective syndrome measurement and reset, and
> the complete detector/observable `Record`.

Three discoveries materially narrow the path:

1. [`quantinuum-dev/pepsy`](https://github.com/quantinuum-dev/pepsy) is the
   closest adjacent product. It contains finite PEPS/PEPO machinery and,
   separately, Kraus trajectories, mid-circuit measurement/reset, and an
   explicit leakage record. At the inspected commit those paths do not compose:
   the trajectory/noise runner accepts MPS/tree optimizers rather than the PEPS
   optimizer, its PEPS sampler rejects physical dimension 3, and its leakage
   model tracks a classical leaked set rather than a coherent qutrit.
2. [`TensorNetworkQuantumSimulator.jl`](https://github.com/JoeyT1994/TensorNetworkQuantumSimulator.jl)
   is the best inspected base for a **qutrit pure-state PEPS adapter**. It has
   physical dimension 3, arbitrary planar graphs, custom gates, controlled
   state-bond truncation, boundary-MPS/BP/exact contraction choices, terminal
   sampling, and GPU backends. It lacks Kraus trajectories, selective
   measurement/reset, and a temporal Record.
3. [`TimeEvolutionPEPO.jl`](https://github.com/jack-dunham/TimeEvolutionPEPO.jl)
   is the closest inspected **open-system PEPO implementation**, but it evolves
   translationally invariant infinite density operators under Lindblad
   dynamics. It is not a finite QEC circuit or a sampled measurement trajectory.

The practical recommendation is therefore:

- retain `pepsy` as the first adjacent-product falsifier;
- use `TensorNetworkQuantumSimulator.jl` as the first qutrit-PEPS adapter
  candidate;
- keep YASTN as the independent finite-PEPS update/contraction comparator;
- treat `TimeEvolutionPEPO.jl` as a PEPO mechanism reference, not as the direct
  carrier;
- do not claim exact or scalable distance-7 behavior before a smaller complete
  Record comparison passes.

This document is a discovery and routing packet. It does not admit an upstream
repository as scientific ground truth and does not authorize a `src/**`
implementation.

## Frozen question and acceptance surface

The question inspected here is:

> Which literature and maintained software can most directly support a finite
> 2D qutrit PEPS or PEPO implementation for non-Pauli leakage across multiple
> QEC rounds, and what complexity and evidence boundaries prevent an exact
> claim?

A direct fit would need all of:

| requirement | why it matters |
|---|---|
| finite open-boundary 2D geometry | The target is a finite rotated XZZX patch, not an infinite unit cell. |
| local physical dimension 3 | Coherent leakage must remain in `|2>`, not only in a classical flag. |
| arbitrary one- and two-site gates | The schedule contains qutrit control operations, not only Hamiltonian annealing. |
| stochastic Kraus application | Dissipative channels must retain their Born branch probabilities. |
| selective measurement and conditional reset | A multi-round syndrome circuit changes state according to the sampled outcome. |
| independent state and environment controls | PEPS bond truncation and network-contraction truncation are different errors. |
| raw branch-mass access | Renormalizing every branch early can hide a wrong probability law. |
| complete temporal Record | Terminal bitstrings or scalar observables are not the product output. |

Ground-state iPEPS optimization, unconditional PEPO evolution, terminal
pure-state sampling, and classical leakage flags are useful adjacent
capabilities but do not satisfy this acceptance surface.

## Complexity boundary: what Schuch does and does not rule out

The newly admitted source-only note is
[`schuch_peps_complexity_prl_98_140506_source_review.md`](../papers/reading_notes/schuch_peps_complexity_prl_98_140506_source_review.md);
its project application is isolated in
[`SCHUCH_PEPS_COMPLEXITY_PROJECT_FIT_AUDIT_2026-07-26.md`](SCHUCH_PEPS_COMPLEXITY_PROJECT_FIT_AUDIT_2026-07-26.md).

| source | exact source result | safe consequence here |
|---|---|---|
| Schuch et al., PRL 98, 140506 (2007), DOI [`10.1103/PhysRevLett.98.140506`](https://doi.org/10.1103/PhysRevLett.98.140506) | “The classical complexity of PEPS,” version-of-record PDF pp. 2--3: the paper-defined exact PEPS norm/unnormalized-expectation/normalized-expectation primitives and general tensor-network contraction are stated to be `#P`-complete under weakly parsimonious reductions. The approximation paragraph on p. 3 transfers difficulty only to the corresponding approximate-counting semantics. | Under the standard `FP != #P` assumption there is no unrestricted exact polynomial solver covering arbitrary instances of those PEPS primitives. This is a worst-case problem boundary, not a distance-7 resource estimate. |
| Haferkamp et al., PRR 2, 013010 (2020), DOI [`10.1103/PhysRevResearch.2.013010`](https://doi.org/10.1103/PhysRevResearch.2.013010) | Main Theorem 1 gives a worst-to-average reduction for exact contraction under an entrywise Gaussian PEPS-data distribution; Appendix A, Theorem 2 reaches exponentially small `2^-poly(N)` precision. | This weakens the objection that only one isolated exact instance is hard, but it does not identify the distribution of QEC-circuit PEPS and does not cover a constant engineering tolerance. |
| Schwarz, Buerschaper, and Eisert, PRA 95, 060102(R) (2017), DOI [`10.1103/PhysRevA.95.060102`](https://doi.org/10.1103/PhysRevA.95.060102) | The main result gives quasi-polynomial approximation of local observables for PEPS satisfying additional physical parent-Hamiltonian structure. | This is the necessary counter-boundary: Schuch must not be rewritten as “all physical PEPS are hard.” No evidence inspected here shows that the dynamic leakage trajectory satisfies the restricted assumptions. |

The correct conclusion is not “PEPS cannot work.” It is:

- local 2D gate updates can be practical while global probabilities remain the
  contraction bottleneck;
- structured finite instances can be tractable;
- any distance-7 result must report both the state bond and the
  environment/contraction bond, and must be compared to an independent
  smaller reference;
- a local residual, CTM convergence test, or terminal sampler certificate is
  not automatically a bound on full Record total variation.

## Incremental literature map

### Already admitted and sufficient for their present roles

| mechanism | admitted sources | retained boundary |
|---|---|---|
| finite PEPS update and boundary contraction | Lubasch et al. | State bond `D` and boundary-MPO/MPS bond are independent; approximate environments need not preserve exact positivity. |
| NTU and closed-loop truncation | Dziarmaga; Evenbly | Local or loop-aware truncation objectives do not certify a temporal Record. |
| iPEPO stability and positivity | Kilda et al.; McKeever and Szymańska; Werner et al. | Unconditional mixed-state observables can be unstable or non-positive at finite bond; these are not sampled QEC trajectories. |
| PEPO construction and 2D operator evolution | Liao et al.; O'Rourke and Chan; Vanhecke et al.; tePEPO | Operator evolution or thermal construction is adjacent, not a selective measurement/reset law. |
| 2D circuit PEPS and terminal sampling | Patra et al.; Rudolph and Tindall | These establish practical pure-state circuit/sampling machinery, not qutrit dissipative multi-round Record faithfulness. |
| software implementation | Rams et al. on YASTN; Naumann et al. on variPEPS | Package capabilities are implementation evidence, not proof that another adapter has the same semantics. |

### Priority sources still outside the current corpus

Directory presence of an old note is not evidence. The following rows are
discovery assignments for clean source reads.

| priority | source and exact locator | reason | current status |
|---|---|---|---|
| P0 | Darmawan and Poulin, PRL 119, 040502 (2017), DOI [`10.1103/PhysRevLett.119.040502`](https://doi.org/10.1103/PhysRevLett.119.040502): PDF p. 1 perfect syndrome assumption; pp. 2--3, Eqs. (1)--(6) and Fig. 1 local CPTP/density-network construction; p. 3 exact and boundary-MPS costs. | The most direct finite 2D surface-code, arbitrary-local-CPTP, non-Pauli PEPS/PEPO bridge. It is code-capacity/single-round with perfect syndrome measurement, not qutrit leakage or a multi-round Record. | Legacy note exists but is excluded; reread the primary version of record and create a current-schema note. |
| P0 | Manabe, Suzuki, and Darmawan, NJP 27, 114512 (2025), DOI [`10.1088/1367-2630/ae1529`](https://doi.org/10.1088/1367-2630/ae1529): Sec. 2.3, Eqs. (8)--(9) qutrit measurement instrument; Sec. 3 MPS/snake carrier; Appendix A, Eq. (A9) Kraus sampling; conclusion on full `d×d` scaling. | The nearest qutrit leakage, Kraus-trajectory, repeated-QEC source. It validates 1D and thin `3×d`, and explicitly motivates PEPS/isoTNS for full 2D. It does not provide a full-2D implementation or Record-TV certificate. | Duplicate legacy notes are excluded; make one clean version-of-record note. |
| P1 | Guo et al., PRL 123, 190501 (2019), DOI [`10.1103/PhysRevLett.123.190501`](https://doi.org/10.1103/PhysRevLett.123.190501): PDF pp. 2--3 gate updates; Methods Eqs. (10)--(15); Appendix B, Eqs. (B1)--(B6). | Separates exact/quasi-exact local pure-state PEPS gate updates from the exponentially costly exact terminal contraction. Noise is left for future work. | New candidate; no current note. |
| P1 | Haferkamp et al. and Schwarz et al., locators above. | They form the average-case and tractable-structure companions needed to keep the Schuch claim calibrated. | New candidates; no current notes. |
| P2 | Czarnik, Dziarmaga, and Corboz, PRB 99, 035115 (2019), DOI [`10.1103/PhysRevB.99.035115`](https://doi.org/10.1103/PhysRevB.99.035115): Sec. IV.B, PDF p. 7, Eq. (19). | Vectorizes a density operator into an iPEPS/isomorphic iPEPO for Lindblad evolution. It is unconditional and overlaps the admitted Kilda/McKeever line. | Historical mechanism candidate, not load-bearing. |

## Library shortlist

Mutable repository facts below were inspected on 2026-07-26. Commit identifiers
are the evidence boundary; a branch name by itself is not.

| disposition | repository | inspected revision / license | direct capability | blocking boundary |
|---|---|---|---|---|
| P0 adjacent-product falsifier | [`quantinuum-dev/pepsy`](https://github.com/quantinuum-dev/pepsy) | `27cb956ec88a739daece90407833bd3c3f8e1d8f`; package metadata `0.3.0`; MIT | Finite PEPS/PEPO optimizers; boundary-MPS, CTMRG, and BP; Torch/JAX/CuPy backends; separate Kraus trajectory, mid-circuit measurement/reset, Stim noise, and `LeakageRecord` machinery. | Noise/trajectory execution is restricted to MPS/tree optimizer families rather than `PepsOptimizer`; PEPS sampling accepts local dimension 2 or 4, not 3; leakage is a classical side set with reset/suppression rules rather than coherent qutrit dynamics. |
| P0 qutrit-PEPS adapter candidate | [`JoeyT1994/TensorNetworkQuantumSimulator.jl`](https://github.com/JoeyT1994/TensorNetworkQuantumSimulator.jl) | `b5d4089849de1cc23806aa8325e8db56a55f2e0b`; package `0.4.4`, latest inspected release `v0.4.2`; MIT | Arbitrary graph TNS/PEPS, built-in qutrit site, custom ITensor gates, SVD/BP updates, boundary-MPS/BP/exact contractions, terminal sampling, CUDA/Metal. | No Kraus/CPTP/Lindblad trajectory, selective measurement/reset, or temporal Record API. |
| P0 independent finite-PEPS comparator | [`yastn/yastn`](https://github.com/yastn/yastn) | repository baseline already pinned at `595bd802ba0753a187b4bf7fd5c6d5007c0170d0`; Apache-2.0 | Finite PEPS, gate evolution, NTU/CTM/BoundaryMPS environments, measurement and sampling, PyTorch/cuTensor backend. | Not a ready QEC trajectory driver; listed diagnostics are not a Record certificate. |
| P1 open-system PEPO mechanism | [`jack-dunham/TimeEvolutionPEPO.jl`](https://github.com/jack-dunham/TimeEvolutionPEPO.jl) | main `fd73b3b4b4b17d7ac69b556980cd9faae669f936`, active dev `ff4480e74a002ef6c43bf7ed9761cb15663c36d6`; `0.1.0-alpha`; MIT | Infinite PEPO Lindblad real-time and finite-temperature evolution; simple/full-environment/NTU; CTMRG/VUMPS; local dissipators; generic TensorKit local spaces. | Pre-alpha and unregistered; infinite translational state, unconditional density evolution, no finite circuit trajectory/Record, no established GPU path. |
| P1 PEPS/PEPO algorithm comparator | [`QuantumKitHub/PEPSKit.jl`](https://github.com/QuantumKitHub/PEPSKit.jl) | `68349a0df85a46a027252945b4bc68b76b3dfd43`; release `v0.8.0`; MIT | Infinite PEPS/PEPO, CTMRG and boundary-MPS contraction, imaginary-time evolution, generic unit cells, PEPO and classical partition functions. | Infinite/ground-state workflow, not a finite measured circuit; real-time `InfinitePEPO` is not implemented at this revision. |
| P1 existing substrate, not independent truth | [`jcmgray/quimb`](https://github.com/jcmgray/quimb) | main `3c89529fe0a3487133a3928201691161e110abdf`; Apache-2.0 | Finite PEPS, contraction planning, simple/full update; current-main circuit PEPS and reverse-observable PEPO simple-update classes. | The circuit classes landed after release `v1.14.0`, so they require a source pin. The project already builds on quimb, so it cannot be the independent referee; the classes do not supply the needed sampler/marginal/Kraus/reset Record workflow. |
| P2 environment comparator | [`jurajHasik/peps-torch`](https://github.com/jurajHasik/peps-torch) | active `master`; MIT | PyTorch/YASTN iPEPS, CTM environments, AD optimization, dense and Abelian-symmetric tensors. | Infinite variational lattice models, not finite QEC circuit trajectories. |
| P2 environment comparator | [`variPEPS/variPEPS_Python`](https://github.com/variPEPS/variPEPS_Python) | repository baseline already pinned at `0edc81acc634e1465264d53f224101d66dcf04e2`; GPL-3.0 | JAX iPEPS, CTMRG/split-CTMRG, observables and differentiation. | Infinite periodic environment, no selective finite Record. |
| P2 HPC ground-state solver | [`issp-center-dev/TeNeS`](https://github.com/issp-center-dev/TeNeS) | active stable `master`; GPL-3.0 | PEPS/CTM 2D lattice solver with MPI/ScaLAPACK. | Ground-state/imaginary-time application, not qutrit trajectory sampling. |

### Why `pepsy` is important but not the immediate qutrit carrier

At the inspected revision:

- `src/pepsy/optimizers/peps/optimizer.py:111`, `:488`, and `:1342` define
  `PepsOptimizer`, its gate loading, and its execution path.
- `src/pepsy/optimizers/noise.py:358-510` defines `TrajectoryChannel` and
  `LeakageRecord`; `:1491-1506` exposes the classical leaked-qubit side state;
  `:1578-1622` implements leaked measurement/reset behavior.
- The noise runner's accepted optimizer families are MPS/tree-oriented; the
  PEPS optimizer is not an accepted trajectory target
  (`src/pepsy/optimizers/noise.py:2234-2261`).
- `src/pepsy/sampling/samplers.py:289-336` restricts the relevant PEPS sampler
  to physical dimension 2 or 4, rejecting dimension 3.
- Leakage is kept in an external leaked-qubit set. On a leakage event the
  computational qubit is reset/suppressed, and seepage returns it stochastically
  to the qubit space; this is not a qutrit amplitude or qutrit Kraus state.

This is a strong prior-product warning: several nouns in the proposed product
already coexist in one repository. It is also a precise differentiator: they
do not yet coexist in one qutrit PEPS execution path.

### Why `TensorNetworkQuantumSimulator.jl` is the first adapter candidate

At the inspected revision:

- `src/siteinds.jl:7-23` registers `"qutrit"`, `"S=1"`, and `"Spin1"` local
  spaces with physical dimension 3.
- `src/sampling.jl:3-105` enumerates outcomes according to the local dimension,
  so a terminal sample is not hard-coded to binary values.
- The public API applies named or raw ITensor gates on arbitrary graph
  vertices and reports SVD update errors.
- Contraction choices include BP, boundary MPS, systematic loop corrections,
  and exact small-network contraction.
- direct/certified sampling reports proposal/target `p/q` information, and
  CUDA/Metal array transfer is documented.

The sampling certificate concerns the state represented by the current
approximate tensor network. It is not an independent certificate that the
state equals the intended noisy circuit, and it is not a bound on a folded
multi-round Record.

The related
[`qiskit-community/qiskit-tnqs`](https://github.com/qiskit-community/qiskit-tnqs)
wrapper was inspected at
`036b99e0b2ae453aae4a3bf9888bb1c5ccf5eb87`. Its qubit frontend maps a fixed
gate set and rejects measurement, reset, and noise instructions. A qutrit
prototype must therefore use the Julia/ITensor layer directly rather than
mistaking the Qiskit wrapper for the required circuit interface.

### Reproduction-only software

| repository | role | why it is not a base |
|---|---|---|
| [`The-iPEPO-Project/iPEPO`](https://github.com/The-iPEPO-Project/iPEPO) at `16327815934438229817279cf226f29a5af28eb0`, GPL-3.0 | Kilda et al. Fortran iPEPO/CTM/simple-update reproduction. | Stale, no public API/release/README, no finite circuit or Record. |
| [`navyTensor/PEPO`](https://github.com/navyTensor/PEPO) at `9ead2f18ffd01cbff2cd71a1fedddb0be5c131e5`, MIT | Liao et al. MATLAB kicked-Ising exact-TNC and Heisenberg-PEPO scripts. | Fixed unitary terminal observables, no density channel or measurement trajectory. |
| [`guochu/RQC`](https://github.com/guochu/RQC), GPL-3.0 | Guo et al. pure-state PEPS circuit implementation, including sequential qubit Born sampling/collapse through full contractions. | Important measurement precedent, but old, qubit-only, no release, and no dissipative/qutrit/QEC Record path. |
| `TN_QSim` | PEPS/PEPO/PEPDO research examples, including thin-surface/leakage material. | No license was found; read-only comparison only, not a distributable dependency. |

## AnySearch and local-retrieval ledger

Search date: **2026-07-26 UTC**. External queries used AnySearch
`academic.search` and `general`; mutable repository facts were then checked
against official GitHub repositories and source at named commits.

### Local RAG/KG first

```text
finite PEPS PEPO qutrit leakage multi-round measurement Record contraction
surface code realistic noise PEPS tensor network simulation
finite open-boundary PEPS
```

The first two were run with `tools/literature_rag.py query`; the last with
`tools/literature_kg.py concept`. They routed to Lubasch, Kilda/McKeever,
Rudolph/Tindall, Liao, Rams/YASTN, and excluded legacy Darmawan/Manabe
material. Local absence was not treated as a literature gap.

### AnySearch academic batches

```text
projected entangled pair states quantum error correction surface code realistic noise tensor network Darmawan Poulin
PEPS quantum circuit simulation sampling mid-circuit measurement open system trajectory
projected entangled pair operator open quantum systems time evolution PEPO
PEPS contraction complexity approximation hardness Schuch Wolf Verstraete Cirac

Tensor-network simulations of quantum error correction codes under realistic noise Darmawan Poulin
2308.08186 leakage tensor network surface code Manabe Suzuki Darmawan
finite PEPS quantum trajectories local measurements reset two-dimensional open systems
PEPO simulation noisy two-dimensional quantum circuits open systems
PEPS sequential projective measurement sampling Born probabilities

2D PEPS stochastic quantum trajectory mid-circuit measurement reset
```

One `finite PEPS quantum trajectories...` request returned a transient search
failure; the final `2D PEPS stochastic...` query reran the missing concept. It
did not return a direct finite-PEPS QEC trajectory/Record result. This is a
bounded search miss, not a field-wide confirmed gap.

### AnySearch code and named-repository batches

```text
YASTN fPEPS GitHub finite PEPS NTU CTM boundary MPS
PEPSKit.jl GitHub PEPS time evolution CTMRG
peps-torch GitHub iPEPS CTM PyTorch
TeNeS GitHub iPEPS tensor network
quimb GitHub PEPS SimpleUpdate FullUpdate tensor network

TensorNetworkQuantumSimulator.jl qutrit sampling PEPS
TimeEvolutionPEPO.jl Lindblad iPEPO
quantinuum pepsy PEPS PEPO leakage trajectory Kraus reset
PEPS PEPO leakage quantum error correction simulator GitHub
quantinuum-dev pepsy GitHub
```

AnySearch directly returned the official
`TensorNetworkQuantumSimulator.jl` and `TimeEvolutionPEPO.jl` repositories. It
did **not** return the `pepsy` repository for either named query; the closest
result for the final query was the official Quantinuum organization listing.
`pepsy` was recovered by following that official organization/source surface
and was then inspected directly. This is why search-engine recall is logged
rather than treated as exhaustive.

## Closure ledger

| evidence question | status |
|---|---|
| Can PEPS represent a 2D qutrit circuit state? | supported |
| Is there a maintained qutrit PEPS software starting point? | supported: `TensorNetworkQuantumSimulator.jl` |
| Is there a nearby product containing both PEPS/PEPO and leakage/noise concepts? | supported: `pepsy`, but its paths do not compose at the inspected revision |
| Does PEPS make arbitrary exact global probabilities polynomial? | blocked under the standard complexity assumption by the Schuch boundary |
| Can PEPO represent unconditional 2D Lindblad evolution? | supported in the literature and adjacent software |
| Was a finite 2D qutrit PEPS/PEPO stochastic-jump implementation with conditional reset and a complete QEC Record found? | missing in this bounded search; not a field-wide confirmed gap |
| Is full distance-7 XZZX leakage Record faithfulness established? | open |

The library shortlist is closed enough to choose an experiment. The
scientific Record bridge remains open.

## Recommended first experiment

Do not begin with distance 7. First freeze one small circuit whose complete
Record can be computed by an independent dense qutrit reference:

1. Pin `pepsy` and `TensorNetworkQuantumSimulator.jl` in separate baseline
   processes; keep their upstream trees pristine.
2. Reproduce one pure qutrit PEPS gate/sampling case in
   `TensorNetworkQuantumSimulator.jl` with no truncation on a small patch.
3. Add Kraus selection, selective measurement, and reset only in a
   repository-owned adapter, preserving every raw branch mass before
   normalization.
4. Sweep the PEPS state bond and the boundary/environment bond independently.
5. Compare conditional outcome probabilities, total raw mass, post-reset
   state, detector/observable bits, full Record total variation, and decoded
   logical error against the independent reference.
6. Require a deliberate corruption to be detected.
7. Only after that passes, attempt distance 5 and then profile whether distance
   7 is a tractable structured instance.

This route tests the real claim. A successful terminal bitstring sample or a
small truncation residual alone would not.
