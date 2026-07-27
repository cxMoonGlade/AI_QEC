# Claim audit — Liu and Clark Rényi-2 disentangler objective and heuristic limits

## Status and decision

This packet audits arXiv:2412.17209v2 for the
optimization-based-disentangling (OBD) objective, its purity interpretation,
and the paper's own limits on local heuristic search and finite-bond
truncation.  The source closes the order-2 Rényi formula and its exact MPS
tensor-contraction use.  It explicitly does not make OBD complete: the paper
gives a concrete instance in which OBD fails while its optimization-free
algorithm (OFD) succeeds.

An independent source-only reviewer checked every claim and locator against
the fixed v2 PDF.  The reviewed note remains outside `CURRENT_CORPUS.toml`
because manifest admission is a separate step not performed by this audit.
This audit changes no implementation and does not by itself register a metric
in `docs/METRICS.md`.

## Assigned closure rows

| row | exact source location | source says | source does not say | status |
|---|---|---|---|---|
| Hybrid state and gauge | Sec. II, Eqs. (1)--(7), PDF p. 3 | A Clifford+T output can be represented as a leading Clifford acting on a residual MPS, and inserted Clifford identities provide a disentangling gauge. | The paper does not instantiate a PEPS residual. | closed |
| OBD score | Sec. IV.A, Eq. (19), PDF p. 9 | At a selected MPS cut after a two-qubit Clifford \(U\), OBD evaluates \(L(U,n)=e^{-S_2(U,n)}\) by an exact double-layer tensor contraction. | The source does not provide an approximate-environment error bar for this contraction. | closed |
| Purity identity | Sec. VI.C, Eqs. (31)--(36), PDF pp. 16--17 | With natural logarithm, \(S_2=-\ln\operatorname{Tr}\rho_A^2\); therefore \(e^{-S_2}=\operatorname{Tr}\rho_A^2\), and the same purity can be written as a Pauli-coefficient sum. | A purity score is not a fidelity or a complete Record-law distance. | closed |
| OBD cost reduction | Sec. IV.A, Eq. (19) and following paragraphs, PDF p. 9 | Precontracting the MPS tensors changes the sequential gate-search cost from a multiplicative \(|\mathrm{Cl}_2|\chi^3\) form to additive \(O(\chi^3)+O(|\mathrm{Cl}_2|)\), with \(|\mathrm{Cl}_2|=11{,}520\). | This does not reduce the source's search to 20 phase-free post-local representatives. | closed |
| Local-sweep heuristic | Sec. IV.A--B, PDF pp. 9--10 | OBD sweeps neighboring pairs until convergence and often, but not always, reproduces the OFD behavior. | No global-optimality or convergence-to-global-minimum theorem is supplied. | closed |
| Explicit heuristic failure | Appendix C, Eq. (C1), PDF pp. 23--24 | For the displayed six Pauli strings on five qubits, an entanglement barrier prevents OBD from moving the needed qubits, whereas OFD finds the long-range \(CX_{1,5}\) disentangler. | The example does not quantify failure frequency for arbitrary states. | closed |
| Finite-bond limitation | Sec. V.A, discussion following Fig. 10, PDF p. 12 | Once bond truncation starts, alternating truncation and disentangling can repeatedly discard small singular-value tails and degrade CAMPS fidelity; the reported procedure stops disentangling when truncation begins. | The paper supplies no accumulated fidelity or observable-error bound for continuing OBD under truncation. | closed |
| PEPS and Record bridge | Full-text scope, especially Secs. IV and VI | The score is formulated for an MPS cut and later CAMPS entropy calculations. | No exact PEPS reduced-density contraction, approximate PEPS environment bound, selective measurement instrument, detector fold, or Record-distance theorem is defined. | missing |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Clifford+T circuit | Commute each \(T=\alpha I+\beta Z\) through the Clifford and insert disentangler identities | Clifford conjugation maps Paulis to Paulis | Leading Clifford \(C\) and residual MPS \(\lvert\psi\rangle\) | Sec. II, Eqs. (1)--(7), PDF p. 3 | complete |
| Canonical MPS tensors at cut \(n|n+1\) and two-qubit Clifford \(U\) | Contract the double-layer network in Eq. (19) with \(U\) and \(U^\dagger\) | The MPS tensors and contraction are exact for the represented state | \(L(U,n)=e^{-S_2(U,n)}\) | Sec. IV.A, Eq. (19), PDF p. 9 | complete |
| Reduced state \(\rho_A\) | Trace out \(\bar A\), square \(\rho_A\), take the trace and negative logarithm | \(\rho\) is a normalized density operator and the logarithm is natural | \(S_2=-\ln\operatorname{Tr}\rho_A^2\) and \(L=\operatorname{Tr}\rho_A^2\) | Sec. VI.C, Eqs. (31)--(36), PDF pp. 16--17 | complete |
| All neighboring-pair two-qubit Clifford candidates | Choose the gate with the best local entropy score and sweep repeatedly | A local improvement is used as a heuristic proxy for a useful disentangler | Stair-step OBD Clifford circuit | Sec. IV.A, PDF p. 9 | complete as algorithm replay, not as an optimality proof |
| Appendix-C Pauli-string sequence | Apply the first strings, observe the entanglement barrier, then compare local OBD with long-range OFD | The five-qubit sequence is exactly the displayed Eq. (C1) fixture | OBD fails; OFD uses \(CX_{1,5}\) | Appendix C, Eq. (C1), PDF pp. 23--24 | complete |

## Project application

The following bridge is a project proposal, not a result proved by Liu and
Clark.

1. For an exact normalized residual state and a fixed physical bipartition,
   minimizing \(S_2\) is exactly equivalent to maximizing the reduced-state
   purity \(L=\operatorname{Tr}\rho_A^2\).  This is a deterministic candidate
   score and requires no fitted threshold.
2. Applying that score to a PEPS residual is source-supported only when the
   finite fixture is contracted exactly into the complete reduced density
   operator.  Replacing it with CTMRG, a boundary MPS, a local singular-value
   tail, or another approximate environment requires a separate bound.
3. The source's OBD enumerates the full two-qubit Clifford group and is a
   local sweep.  Combining its score with Chang et al.'s independently
   verified 20 post-local phase-free representatives is an
   exact-small project construction, not a method stated by either paper.
4. The Appendix-C failure is a required negative control against claiming
   that local entropy sweeps are complete.  An exact-small test should compare
   a 20-representative minimum against an independently enumerated
   720-action minimum at the same cut rather than treating OBD convergence as
   ground truth.
5. Rényi-2/purity remains a state-level quantity.  It cannot register or
   certify a detector/observable Record metric without a separate owner,
   independent value test, and source-backed bridge.

## Competing evidence and kill conditions

- Chang et al. optimize order-\(1/2\) Rényi entropy rather than order 2.
  Both are invariant under output-local unitaries because both depend on the
  Schmidt spectrum, but their numerical rankings of non-equivalent gates need
  not coincide.
- The source itself kills a blanket OBD-completeness claim through Appendix
  C.  Any implementation that treats “sweep converged” as “global minimum
  found” contradicts this limitation.
- Kill the purity score if input norms are non-finite/non-positive or if the
  independently constructed reduced density matrix is not finite, Hermitian,
  unit trace, and positive within a declared numerical comparison.
- Kill 20-candidate completeness if its minimum differs from the independently
  enumerated 720-action minimum on any frozen exact fixture.
- Kill scalable use if an approximate PEPS contraction is substituted without
  a certified error interval capable of preserving the candidate ordering.
- Kill any Record-faithfulness claim based solely on lower \(S_2\), higher
  purity, lower bond dimension, or OBD convergence.

## Source-local verdict

- read_status: complete
- evidence_status: persisted and source-only reviewed, not manifest-admitted
- assigned-row status: score, purity bridge, complexity, and heuristic
  limitations closed; PEPS/Record bridge missing
- downstream permission: source-note review and exact-small preregistration
  design only; no metric registration, implementation, or scalable claim

