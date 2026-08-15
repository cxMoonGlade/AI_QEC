# BLP 0908.0238v2 — non-Markovian witness source audit

Status: source-only audit for the GCAPEPS finite-memory benchmark, 2026-07-29.

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| trace-distance metric | Eq. (1), PDF p. 1 | \(D(\rho_1,\rho_2)=\frac12\operatorname{tr}|\rho_1-\rho_2|\), with \(0\le D\le1\) | It does not define a PEPS bond or truncation metric. | closed |
| Markov contraction | Eqs. (2), (5), and (9), PDF pp. 1–2 | CPT maps contract trace distance; divisible dynamics therefore cannot increase it for a fixed input pair. | It does not prove that every modern notion of quantum Markovianity is equivalent to BLP divisibility. | closed at the source's definition |
| positive-backflow witness | Eqs. (10)–(12), PDF pp. 2–3 | A positive derivative of trace distance for at least one input pair witnesses non-Markovian behavior; the integrated optimized positive part defines \(\mathcal N(\Phi)\). | A fixed pair with no revival does not prove Markovianity, and an unoptimized positive sum is only a lower bound on \(\mathcal N\). | closed |
| finite-environment nonmonotonicity | Eq. (14) and following paragraphs, PDF p. 4 | The central-spin example gives periodic trace-distance oscillations and repeated information exchange with a finite spin bath. | It does not predict monotonic entanglement or bond growth. | closed |
| implementation feasibility | concluding paragraphs, PDF p. 4 | State tomography at several times can test whether trace distance increased without identifying the environment model. | It gives no PEPS, GCAPEPS, timing, or truncation algorithm. | closed only for the witness computation |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| two reduced density matrices | form \(\rho_1-\rho_2\), take the trace norm, and multiply by \(1/2\) | both are physical states on the same Hilbert space | \(D(\rho_1,\rho_2)\in[0,1]\) | Eq. (1), PDF p. 1 | complete |
| one fixed initial pair and a common dynamical map | evaluate \(D_n\) at successive times | the same map acts on both initial states | trace-distance trajectory | Eqs. (1), (10), PDF pp. 1–2 | complete |
| trace-distance trajectory | discretize the continuous positive-rate construction by summing only positive successive increments | discrete sampling reports only observed revivals | a lower-bound fixed-pair witness; positive means BLP non-Markovian | audit derivation from Eqs. (10)–(12), PDF pp. 2–3; this discrete formula is not printed in BLP | complete as a project derivation, not a source equation |
| all possible initial pairs and continuous dynamics | maximize the integrated positive derivative | exact reduced dynamics and the optimization are available | \(\mathcal N(\Phi)\) | Eq. (11), PDF p. 2 | complete |

## Project application

The benchmark may hand-build two exact dense joint system-memory evolutions
from a neutral collision fixture, trace out the memory row after every round,
and evaluate the BLP trace distance on the system row. Both evolutions must use
the same memory state, collision mask, gate order, and unitary parameters. A
strictly positive round-to-round increment above the preregistered numerical
guard is an operational witness for that frozen fixture.

The benchmark will not optimize over all input pairs. Its reported positive
sum is therefore a lower-bound witness, not the source's full
\(\mathcal N(\Phi)\). A zero observed sum is `NO_WITNESS_FOR_REGISTERED_PAIR`,
not `MARKOVIAN`. Candidate PEPS bonds, discarded weights, state fidelity, and
system-memory entropy remain separate diagnostics.

## Competing evidence and kill conditions

- The BLP definition is one operational notion of non-Markovianity. The project
  will not relabel CP-divisibility, process-tensor memory, or conditional
  multi-time dependence as equivalent without a separate bridge.
- A positive increment computed from different collision masks or different
  maps for the two initial states is invalid.
- A candidate-only revival cannot establish the fixture mechanism because
  truncation itself can create a spurious revival; the witness is computed by
  an independent dense route.
- Entanglement or bond growth without trace-distance revival is not a BLP
  witness.

## Source-local verdict

- read_status: complete
- evidence_status: persisted
- assigned-row status: closed
