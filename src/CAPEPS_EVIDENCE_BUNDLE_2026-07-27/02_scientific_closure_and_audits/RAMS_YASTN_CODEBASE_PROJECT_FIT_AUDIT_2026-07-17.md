# Claim audit — YASTN codebase paper and carrier relevance

## Status and decision

Retain Rams et al., *YASTN: Yet another symmetric tensor networks; A Python library for Abelian
symmetric tensor network calculations*, as an adjacent software-capability and implementation
source. It documents block-sparse symmetric tensors plus MPS/fPEPS algorithms and benchmarked CTM
execution. It is not a primary proof of MPS truncation faithfulness, PEPS FET semantics, or QEC
Record correctness.

## Assigned closure rows

| row | exact source location | source says | source does not say | status |
|---|---|---|---|---|
| Package architecture | Sec. 2, Fig. 2, PDF p. 4 | YASTN separates Abelian symmetry/block structure from dense numerical backends and builds MPS/fPEPS modules above that tensor layer. | The architecture diagram is not a scientific carrier certification. | closed |
| Symmetric tensor rule | Sec. 2.1, Eqs. (6)--(10), PDF pp. 5--6 | Charge conservation selects nonzero blocks and defines the block-sparse tensor representation. | Block sparsity alone says nothing about approximation or Record error. | closed |
| Algorithm scope | Sec. 2.3, PDF p. 8 | The MPS module includes finite MPS DMRG, TDVP, and overlap maximization; the fPEPS module includes finite/infinite states and NTU/cluster/full-update evolution. | The article does not specify a QEC selective-measurement adapter or its emitted schema. | closed |
| CTM execution | Sec. 3 and Fig. 3, PDF p. 9 | CTM approximates an infinite iPEPS environment using finite corner/transfer tensors and SVD projectors controlled by environment dimension `chi`. | This is not the FET bond objective and does not make the environment exact. | closed |
| Thermal example | Sec. 3.3, Eq. (17), Figs. 6, PDF pp. 13--14 | A purified finite-temperature Hubbard iPEPS is evolved with NTU and evaluated with CTM; Abelian symmetry reduces memory and time in the reported setup. | The benchmark is not a multi-round QEC trajectory Record. | closed |
| Record bridge | Full-text scope and Sec. 4, PDF pp. 14--15 | The paper reports software design and many-body benchmark performance. | It gives no branch-mass reconciliation, detector XOR construction, logical-observable law, Record TV, or LER certification. | missing |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Abelian group, leg charges, and tensor charge | Apply charge-conservation selection and serialize allowed blocks over a dense backend | The requested symmetry is Abelian and leg metadata are consistent | Block-sparse `yastn.Tensor` | Sec. 2.1, Eqs. (6)--(10), PDF pp. 5--6 | complete |
| Symmetric tensor objects | Compose finite-MPS or fPEPS algorithms on the higher-level modules | The implementation supports the listed method and backend | Algorithm-specific MPS/fPEPS computation | Sec. 2.3, Fig. 2, PDF pp. 4, 8 | complete |
| iPEPS and target environment dimension | Iterate CTM contractions, fusions, and SVD projections | Finite `chi` is sufficient for the reported observable convergence | Approximate environment and benchmark observables | Sec. 3, Fig. 3, PDF p. 9 | complete |

## Project application

- The paper can support a statement that mature tensor software exposes finite-MPS TDVP and
  finite/infinite fPEPS update machinery, but it does not certify this repository's adapter wiring or
  record semantics.
- Its YASTN benchmarks are performance/capability evidence. They do not replace independent dense/SVD
  references, corruption falsifiers, or complete Record comparisons required by the simulator contract.
- The source is adjacent to future carrier engineering, not a reason to promote `carrier/mps`, PEPS,
  or PEPO to a stronger scientific status.

## Competing evidence and kill conditions

- Paeckel and Jaschke/Sander are the more direct sources for MPS evolution/truncation and quantum
  trajectories; Evenbly is the direct FET source.
- Kill any use that cites a listed library capability as proof that the exact project implementation
  realizes the same operation or preserves a QEC Record distribution.

## Source-local verdict

- read_status: complete
- evidence_status: persisted
- assigned rows: five closed, one missing
- project fit: adjacent implementation survey/codebase evidence only
